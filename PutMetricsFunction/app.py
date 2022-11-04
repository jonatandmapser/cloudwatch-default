import json
import logging

import boto3
from botocore.config import Config

ec2_cient = boto3.client("ec2")
rds = boto3.client("rds")
CW_client = boto3.client("cloudwatch")
sns_client = boto3.client("sns")
regions = ["eu-west-1"]
logger = logging.getLogger()
logger.setLevel(logging.INFO)
aws_account_id = ""
instances_rds = []
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
instances_all = []
instances_linux = []
instances_windows = []
volumenes = []


def put_metrics_ebs(lambda_payload,aws_account_id):
    ##ALARMA DE BURST BALANCE MENOR DE 10%#####
    CW_client.put_metric_alarm(
        AlarmName="Volume Queue Length " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=3,
        MetricName="VolumeQueueLength",
        Namespace="AWS/EBS",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=1,
        AlarmDescription="Alarm when Volume Queue Length less than 10",
        Dimensions=[
            {"Name": "VolumeId", "Value": lambda_payload["instancia"]},
        ],
    )


####FUNCION QUE AÑADE LAS ALARMAS DE LAS INSTANCIAS WINDOWS####
def put_metrics_win(lambda_payload,aws_account_id):

    ##ALARMA DE USO DE CPU MAYOR DE 95%#####
    CW_client.put_metric_alarm(
        AlarmName="CPU_Utilization " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanThreshold",
        EvaluationPeriods=3,
        MetricName="CPUUtilization",
        Namespace="AWS/EC2",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=90.0,
        AlarmDescription="Alarm when server CPU exceeds 95%",
        Dimensions=[
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
        ],
    )

    ##ALARMA DE CREDIT BALANCE MENOR DE 10%#####
    CW_client.put_metric_alarm(
        AlarmName="Credit Balance " + lambda_payload["instancia"],
        ComparisonOperator="LessThanThreshold",
        EvaluationPeriods=3,
        MetricName="CPUCreditBalance",
        Namespace="AWS/EC2",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Minimum",
        Threshold=10.0,
        AlarmDescription="Alarm when Credit Balance less than 10",
        Dimensions=[
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
        ],
    )

    ##ALARMA DE USO DE MEMORIA MAYOR O IGUAL A 99%#####
    CW_client.put_metric_alarm(
        AlarmName="Memory % Committed Bytes In Use " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=3,
        MetricName="Memory % Committed Bytes In Use",
        Namespace="CWAgent",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=90.0,
        AlarmDescription="Alarm when Ram greater than 99",
        Dimensions=[
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
            {"Name": "ImageId", "Value": lambda_payload["imageId"]},
            {"Name": "objectname", "Value": "Memory"},
            {"Name": "InstanceType", "Value": lambda_payload["instanceType"]},
        ],
    )

    ##ALARMA DE USO DE DISCO MAYOR O IGUAL A 95%#####
    CW_client.put_metric_alarm(
        AlarmName="LogicalDisk % Free Space " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=3,
        MetricName="LogicalDisk % Free Space",
        Namespace="CWAgent",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=95.0,
        AlarmDescription="Alarm when disk free space less than 5",
        Dimensions=[
            {"Name": "instance", "Value": lambda_payload["instance"]},
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
            {"Name": "ImageId", "Value": lambda_payload["imageId"]},
            {"Name": "objectname", "Value": "LogicalDisk"},
            {"Name": "InstanceType", "Value": lambda_payload["instanceType"]},
        ],
    )


def put_metrics_lin(lambda_payload,aws_account_id):

    CW_client.put_metric_alarm(
        AlarmName="CPU_Utilization " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanThreshold",
        EvaluationPeriods=3,
        MetricName="CPUUtilization",
        Namespace="AWS/EC2",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=90.0,
        AlarmDescription="Alarm when server CPU exceeds 95%",
        Dimensions=[
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
        ],
    )

    ##ALARMA DECREDIT BALANCE MENOR DE 10%#####
    CW_client.put_metric_alarm(
        AlarmName="Credit Balance " + lambda_payload["instancia"],
        ComparisonOperator="LessThanThreshold",
        EvaluationPeriods=3,
        MetricName="CPUCreditBalance",
        Namespace="AWS/EC2",
        Period=300,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Minimum",
        Threshold=10.0,
        AlarmDescription="Alarm when Credit Balance less than 10",
        Dimensions=[
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
        ],
    )

    ##ALARMA DE USO DE RAM MAYOR DE 99%#####
    CW_client.put_metric_alarm(
        AlarmName="Mem Used Percent " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=3,
        MetricName="mem_used_percent",
        Namespace="CWAgent",
        Period=60,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=90.0,
        AlarmDescription="Alarm when Ram greater than 99",
        Dimensions=[
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
            {"Name": "ImageId", "Value": lambda_payload["imageId"]},
            {"Name": "InstanceType", "Value": lambda_payload["instanceType"]},
        ],
    )

    ##ALARMA DE USO DE DISCO MAYOR DE 95%#####
    CW_client.put_metric_alarm(
        AlarmName="disk_used_percent " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=3,
        MetricName="disk_used_percent",
        Namespace="CWAgent",
        Period=60,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=95.0,
        AlarmDescription="Alarm when Disk greater than 95",
        Dimensions=[
            {"Name": "path", "Value": "/"},
            {"Name": "InstanceId", "Value": lambda_payload["instancia"]},
            {"Name": "ImageId", "Value": lambda_payload["imageId"]},
            {"Name": "InstanceType", "Value": lambda_payload["instanceType"]},
            {"Name": "device", "Value": lambda_payload["device"]},
            {"Name": "fstype", "Value": lambda_payload["fstype"]},
        ],
    )


def put_metrics_rds(lambda_payload,aws_account_id):

    CW_client.put_metric_alarm(
        AlarmName="CPU_Utilization RDS " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanThreshold",
        EvaluationPeriods=3,
        MetricName="CPUUtilization",
        Namespace="AWS/RDS",
        Period=300,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=90.0,
        AlarmDescription="Alarm when RDS CPU exceeds 90%",
        Dimensions=[
            {"Name": "DBInstanceIdentifier", "Value": lambda_payload["instancia"]},
        ],
    )

    ##ALARMA DECREDIT BALANCE MENOR DE 10%#####
    CW_client.put_metric_alarm(
        AlarmName="Freeable Memory RDS " + lambda_payload["instancia"],
        ComparisonOperator="LessThanThreshold",
        EvaluationPeriods=3,
        MetricName="FreeableMemory",
        Namespace="AWS/RDS",
        Unit="Bytes",
        Period=300,
        ActionsEnabled=True,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=1000000000,
        AlarmDescription="Alarm when Freeable Memory RDS less than 10 GB",
        Dimensions=[
            {"Name": "DBInstanceIdentifier", "Value": lambda_payload["instancia"]},
        ],
    )

    ##ALARMA DE USO DE RAM MAYOR DE 99%#####
    CW_client.put_metric_alarm(
        AlarmName="Free Storage Space RDS " + lambda_payload["instancia"],
        ComparisonOperator="LessThanThreshold",
        EvaluationPeriods=3,
        MetricName="FreeStorageSpace",
        Namespace="AWS/RDS",
        Period=60,
        ActionsEnabled=True,
        Unit="Bytes",
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=10000000000,
        AlarmDescription="Alarm when Free Storage Space RDS less than 10GB",
        Dimensions=[{"Name": "DBInstanceIdentifier", "Value": lambda_payload["instancia"]}],
    )

    ##ALARMA DE USO DE DISCO MAYOR DE 95%#####
    CW_client.put_metric_alarm(
        AlarmName="Disk Queue Depth RDS " + lambda_payload["instancia"],
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=3,
        MetricName="DiskQueueDepth",
        Namespace="AWS/RDS",
        Period=60,
        AlarmActions=["arn:aws:sns:eu-west-1:"+str(aws_account_id)+":CorreoSoporte"],
        Statistic="Average",
        Threshold=1,
        AlarmDescription="Alarm when Disk Queue Depth RDS greater than 1",
        Dimensions=[{"Name": "DBInstanceIdentifier", "Value": lambda_payload["instancia"]}],
    )

def lambda_handler(event, context):
    aws_account_id = boto3.client("sts").get_caller_identity().get("Account")
    print(aws_account_id)
    response = ec2.describe_instances()
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
                    logger.info(j["BlockDeviceMappings"][0]["Ebs"]["VolumeId"])
                    logger.info(f"Volumen ID: {j['BlockDeviceMappings'][0]['Ebs']['VolumeId']}")
                    for vol in j["BlockDeviceMappings"]:
                        volumenes.append(
                            {"VolumenId": vol["Ebs"]["VolumeId"]}
                        )
                    region = j["Placement"]["AvailabilityZone"]
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

    
    ####CREAR ALARMAS RDS #########
    db_instances = rds.describe_db_instances()
    for i in db_instances["DBInstances"]:
        instances_rds.append(i["DBInstanceIdentifier"])
    
    for i in instances_rds:
        lambda_payload = {
            "instancia": i,
        }
        put_metrics_rds(lambda_payload,aws_account_id)
    #####CREAR ALARMAS RDS #########
    
    ####FUNCION QUE AÑADE LAS ALARMAS DE LOS VOLUMENES####
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
        if response["Metrics"] == []:
            enviosns = sns_client.publish(
                TopicArn=f"arn:aws:sns:eu-west-1:{aws_account_id}:CorreoSoporte",
                Message="Agente Cloudwatch inactivo maquina windows: "
                + i["InstanceId"]
                + f" cuenta AWS: {aws_account_id}",
                Subject="Agente Cloudwatch inactivo maquina windows: "
                + i["InstanceId"]
                + f" cuenta AWS: {aws_account_id}",
            )
        else:
            for metrics in response["Metrics"]:
                lambda_payload = {
                    "tipo": "win",
                    "instancia": i["InstanceId"],
                    "imageId": i["ImageId"],
                    "instanceType": i["InstanceType"],
                    "instance": metrics["Dimensions"][0]["Value"],
                }
                put_metrics_win(lambda_payload,aws_account_id)
                logger.info(f"response windows: {response}")
    
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
        if response["Metrics"] == []:
            enviosns = sns_client.publish(
                TopicArn=f"arn:aws:sns:eu-west-1:{aws_account_id}:CorreoSoporte",
                Message="Agente Cloudwatch inactivo maquina linux: "
                + i["InstanceId"]
                + f" cuenta AWS: {aws_account_id}",
                Subject="Agente Cloudwatch inactivo maquina linux: "
                + i["InstanceId"]
                + f" cuenta AWS: {aws_account_id}",
            )
        else:
            for metrics in response["Metrics"]:
                lambda_payload = {
                    "tipo": "lin",
                    "instancia": i["InstanceId"],
                    "imageId": i["ImageId"],
                    "instanceType": i["InstanceType"],
                    "path": metrics["Dimensions"][0]["Value"],
                    "device": metrics["Dimensions"][4]["Value"],
                    "fstype": metrics["Dimensions"][5]["Value"],
                }
                put_metrics_lin(lambda_payload,aws_account_id)
                logger.info(f"response linux: {response}")
    
    for v in volumenes:
        lambda_payload = {"tipo": "ebs", "instancia": v["VolumenId"]}
    
        put_metrics_ebs(lambda_payload,aws_account_id)
        logger.info(f"response volumen: {response}")
