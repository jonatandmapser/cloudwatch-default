import json
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


CW_client = boto3.client("cloudwatch")
RDS_client = boto3.client("rds")
ec2_client = boto3.client("ec2")
instances_rds = []
instances_all = []
instances_linux = []
instances_windows = []
volumenes = []
instances_rds = []
region = 'eu-west-1'

def lambda_handler(event, context):
    aws_account_id = boto3.client("sts").get_caller_identity().get("Account")
    response = ec2_client.describe_instances()
    for i in response["Reservations"]:
        for j in i["Instances"]:
            # comprobar el estado de la instancia y si es terminada no hacer nada
            if j["State"]["Name"] != "terminated":
                if j["State"]["Name"] != "stopped":
                    instances_all.append(
                        {
                            "InstanceId": j["InstanceId"],
                            "InstanceType": j["InstanceType"],
                            "ImageId": j["ImageId"],
                        }
                    )
                    for vol in j["BlockDeviceMappings"]:
                        volumenes.append(
                            {"VolumenId": vol["Ebs"]["VolumeId"]}
                        )
                    region = j["Placement"]["AvailabilityZone"][:-1]
                    print(region)
                    try:
                        # TODO: write code...
                        if j['PlatformDetails'] == "Linux/UNIX":
                            instances_linux.append(
                                {
                                    "InstanceId": j["InstanceId"],
                                    "InstanceType": j["InstanceType"],
                                    "ImageId": j["ImageId"],
                                }
                            )
                        else:
                            instances_windows.append(
                                {
                                    "InstanceId": j["InstanceId"],
                                    "InstanceType": j["InstanceType"],
                                    "ImageId": j["ImageId"],
                                }
                            )
                    except Exception as e:
                        print(e)
            
            for t in j["Tags"]:
                if "no-monitoring" in t["Key"]:
                    for i in instances_all:
                        if j["InstanceId"] in i["InstanceId"]:
                            instances_all.remove(i)
                    for i in instances_linux:
                        if j["InstanceId"] in i["InstanceId"]:
                            instances_linux.remove(i)
                    for i in instances_windows:
                        if j["InstanceId"] in i["InstanceId"]:
                            instances_windows.remove(i)
                    for v in volumenes:
                        if vol["Ebs"]["VolumeId"] in volumenes:
                            volumenes.remove(v) 

        db_instances = RDS_client.describe_db_instances()
        for i in db_instances["DBInstances"]:
            instances_rds.append(i["DBInstanceIdentifier"])

        ############EC2###########
        Mem_Used_percent_win_template = '["CWAgent", "Memory % Committed Bytes In Use", "InstanceId", "{}", "ImageId", "{}", "objectname", "Memory", "InstanceType", "{}"]'
        Mem_Used_percent_win_array = []
        Mem_Used_percent_lin_template = '["CWAgent", "mem_used_percent", "InstanceId", "{}", "ImageId", "{}", "InstanceType", "{}"]'
        Mem_Used_percent_lin_array = []
        Disk_Used_percent_lin_template = '["CWAgent", "disk_used_percent", "path", "/", "InstanceId", "{}", "ImageId", "{}", "InstanceType", "{}", "device", "{}", "fstype", "{}"]'
        Disk_Used_percent_lin_array = []
        Disk_Used_percent_win_template = '["CWAgent", "LogicalDisk % Free Space", "instance", "{}", "InstanceId", "{}", "ImageId", "{}", "objectname", "LogicalDisk", "InstanceType", "{}"]'
        Disk_Used_percent_win_array = []
        CPUUtilization_template = '["AWS/EC2", "CPUUtilization", "InstanceId", "{}"]'
        CPUUtilization_array = []
        CPUCreditBalance_template = (
            '["AWS/EC2", "CPUCreditBalance", "InstanceId", "{}"]'
        )
        CPUCreditBalance_array = []
        VolumeQueueLength_template = '["AWS/EBS", "VolumeQueueLength", "VolumeId", "{}"]'
        VolumeQueueLength_array = []
        StatusCheckFailed_Instance = (
            '["AWS/EC2", "StatusCheckFailed_Instance", "InstanceId", "{}"]'
        )
        StatusCheckFailed_Instance_array = []
        StatusCheckFailed_System = (
            '["AWS/EC2", "StatusCheckFailed_System", "InstanceId", "{}"]'
        )
        StatusCheckFailed_System_array = []
        ############EC2###########

        ############RDS###########
        CPUUtilizationRDS_template = (
            '["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "{}"]'
        )
        FreeableMemory_template = (
            '["AWS/RDS", "FreeableMemory", "DBInstanceIdentifier", "{}"]'
        )
        FreeStorageSpace_template = (
            '["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", "{}"]'
        )
        DiskQueueDepth_template = (
            '["AWS/RDS", "DiskQueueDepth", "DBInstanceIdentifier", "{}"]'
        )

        CPUUtilizationRDS_array = []
        FreeableMemory_array = []
        FreeStorageSpace_array = []
        DiskQueueDepth_array = []
        ############RDS###########

        # Añadimos las ID de las intancias en las metricas
        for i in instances_all:
            StatusCheckFailed_Instance_array.append(
                StatusCheckFailed_Instance.format(i["InstanceId"])
            )
            StatusCheckFailed_System_array.append(StatusCheckFailed_System.format(i["InstanceId"]))
            CPUUtilization_array.append(CPUUtilization_template.format(i["InstanceId"]))
            CPUCreditBalance_array.append(CPUCreditBalance_template.format(i["InstanceId"]))
        for i in instances_linux:
            response = CW_client.list_metrics(
                MetricName="disk_used_percent",
                Namespace="CWAgent",
                Dimensions=[
                    {"Name": "ImageId", "Value": i["ImageId"]},
                    {"Name": "InstanceId", "Value": i["InstanceId"]},
                    {"Name": "path", "Value": "/"},
                ],
            )
            for metrics in response["Metrics"]:
                Disk_Used_percent_lin_array.append(
                    Disk_Used_percent_lin_template.format(
                        i["InstanceId"],
                        i["ImageId"],
                        i["InstanceType"],
                        metrics["Dimensions"][4]["Value"],
                        metrics["Dimensions"][5]["Value"],
                    )
                )

            Mem_Used_percent_lin_array.append(
                Mem_Used_percent_lin_template.format(i["InstanceId"], i["ImageId"], i["InstanceType"])
            )
        for i in instances_windows:
            response = CW_client.list_metrics(
                MetricName="LogicalDisk % Free Space",
                Namespace="CWAgent",
                Dimensions=[
                    {"Name": "instance"},
                    {"Name": "InstanceId", "Value": i["InstanceId"]},
                    {"Name": "ImageId", "Value": i["ImageId"]},
                    {"Name": "objectname"},
                    {"Name": "InstanceType", "Value": i["InstanceType"]},
                ],
            )
            for metrics in response["Metrics"]:
                Disk_Used_percent_win_array.append(
                    Disk_Used_percent_win_template.format(
                        metrics["Dimensions"][0]["Value"],
                        i["InstanceId"],
                        i["ImageId"],
                        i["InstanceType"],
                    )
                )
            Mem_Used_percent_win_array.append(
                Mem_Used_percent_win_template.format(i["InstanceId"], i["ImageId"], i["InstanceType"])
            )
        for v in volumenes:
            VolumeQueueLength_array.append(VolumeQueueLength_template.format(v['VolumenId']))

        for i in instances_rds:
            CPUUtilizationRDS_array.append(CPUUtilizationRDS_template.format(i))
            FreeableMemory_array.append(FreeableMemory_template.format(i))
            FreeStorageSpace_array.append(FreeStorageSpace_template.format(i))
            DiskQueueDepth_array.append(DiskQueueDepth_template.format(i))

        ############EC2###########
        CPUUtilization_string = ",".join(CPUUtilization_array)
        CPUCreditBalance_string = ",".join(CPUCreditBalance_array)
        StatusCheckFailed_Instance_string = ",".join(StatusCheckFailed_Instance_array)
        StatusCheckFailed_System_string = ",".join(StatusCheckFailed_System_array)
        Mem_Used_percent_lin_string = ",".join(Mem_Used_percent_lin_array)
        Mem_Used_percent_win_string = ",".join(Mem_Used_percent_win_array)
        Disk_Used_percent_win_string = ",".join(Disk_Used_percent_win_array)
        Disk_Used_percent_lin_string = ",".join(Disk_Used_percent_lin_array)
        VolumeQueueLength_string = ",".join(VolumeQueueLength_array)
        ############EC2###########

        ############RDS###########
        CPUUtilizationRDS_string = ",".join(CPUUtilizationRDS_array)
        FreeableMemory_string = ",".join(FreeableMemory_array)
        FreeStorageSpace_string = ",".join(FreeStorageSpace_array)
        DiskQueueDepth_string = ",".join(DiskQueueDepth_array)
        ############RDS###########

        ############EC2###########
    CPUUtilization_instances = r'{"type": "metric", "x": 12, "y": 1, "width": 12, "height": 6, "properties": {"metrics": [template], "view": "timeSeries", "stacked": false, "region": "eu-west-1", "stat": "Average", "period": 5, "title": "CPU Usage" }}'.replace(
        "template", CPUUtilization_string
    )
    CPUCreditBalance_instances = (
        r'{"type": "metric", "x": 0, "y": 1, "width": 12, "height": 6, "properties": {"metrics": ['
        + CPUCreditBalance_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "CPU Credit Balance" }}'
    )
    Mem_Used_percent_lin_instances = (
        r'{"type": "metric", "x": 12, "y": 2, "width": 12, "height": 6, "properties": {"metrics": ['
        + Mem_Used_percent_lin_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "RAM_Usage_Linux" }}'
    )
    Mem_Used_percent_win_instances = (
        r'{"type": "metric", "x": 0, "y": 2, "width": 12, "height": 6, "properties": {"metrics": ['
        + Mem_Used_percent_win_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "RAM_Usage_Windows" }}'
    )
    Disk_Used_percent_win_instances = (
        r'{"type": "metric", "x": 0, "y": 3, "width": 12, "height": 6, "properties": {"metrics": ['
        + Disk_Used_percent_win_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "Disk_Usage_Windows" }}'
    )
    Disk_Used_percent_lin_instances = (
        r'{"type": "metric", "x": 12, "y": 3, "width": 12, "height": 6, "properties": {"metrics": ['
        + Disk_Used_percent_lin_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "Disk_Usage_Linux" }}'
    )
    StatusCheckFailed_Instance_instances = (
        r'{"type": "metric", "x": 0, "y": 4, "width": 12, "height": 6, "properties": {"metrics": ['
        + StatusCheckFailed_Instance_string
        + r'], "view": "singleValue", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 300, "title": "StatusCheckFailed_Instance" }}'
    )
    StatusCheckFailed_System_instances = (
        r'{"type": "metric", "x": 12, "y": 4, "width": 12, "height": 6, "properties": {"metrics": ['
        + StatusCheckFailed_System_string
        + r'], "view": "singleValue", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 300, "title": "StatusCheckFailed_System" }}'
    )
    VolumeQueueLength_instances = (
        r'{"type": "metric", "x": 0, "y": 5, "width": 24, "height": 6, "properties": {"metrics": ['
        + VolumeQueueLength_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "VolumeQueueLength" }}'
    )

    ############RDS###########
    CPUUtilizationRDS_instances = (
        r'{"type": "metric", "x": 0, "y": 6, "width": 24, "height": 6, "properties": {"metrics": ['
        + CPUUtilizationRDS_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "CPU Utilization RDS" }}'
    )
    FreeableMemory_instances = (
        r'{"type": "metric", "x": 12, "y": 6, "width": 24, "height": 6, "properties": {"metrics": ['
        + FreeableMemory_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "Freeable Memory RDS" }}'
    )
    FreeStorageSpace_instances = (
        r'{"type": "metric", "x": 0, "y": 7, "width": 24, "height": 6, "properties": {"metrics": ['
        + FreeStorageSpace_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "Free Storage Space RDS" }}'
    )
    DiskQueueDepth_instances = (
        r'{"type": "metric", "x": 12, "y": 7, "width": 24, "height": 6, "properties": {"metrics": ['
        + DiskQueueDepth_string
        + r'], "view": "timeSeries", "stacked": false, "region": "'
        + region
        + r'", "stat": "Average", "period": 5, "title": "Disk Queue Depth RDS" }}'
    )

    response = CW_client.put_dashboard(
        DashboardName="Cloudwatch-Default",
        DashboardBody='{"widgets": ['
        + CPUUtilization_instances
        + ","
        + CPUCreditBalance_instances
        + ","
        + Mem_Used_percent_lin_instances
        + ","
        + Mem_Used_percent_win_instances
        + ","
        + Disk_Used_percent_win_instances
        + ","
        + Disk_Used_percent_lin_instances
        + ","
        + VolumeQueueLength_instances
        + ","
        + StatusCheckFailed_Instance_instances
        + ","
        + StatusCheckFailed_System_instances
        + ","
        + CPUUtilizationRDS_instances
        + ","
        + FreeableMemory_instances
        + ","
        + FreeStorageSpace_instances
        + ","
        + DiskQueueDepth_instances
        + "]}",
    )
    
    print(response)
