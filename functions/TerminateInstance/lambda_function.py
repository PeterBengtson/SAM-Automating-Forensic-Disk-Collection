import os
import boto3

ROLE_NAME = os.environ['ROLE_NAME']

sts_client = boto3.client('sts')


def lambda_handler(params, _context):
    print(params)

    if params['Terminate'] != 'Yes':
        print("Termination aborted.")
        return True

    region = params['Region']
    account_id = params['AwsAccountId']
    instance_arn = params['InstanceARN']
    instance_id = instance_arn.rsplit('/', 1)[1]

    client = get_client('ec2', account_id, region)

    print(
        f"Disabling API termination for instance {instance_id} in account {account_id}, region {region}...")
    try:
        response = client.modify_instance_attribute(
            DisableApiTermination={
                'Value': False
            },
            InstanceId=instance_id,
        )
        print(response)
    except Exception:
        pass

    print(
        f"Terminating instance {instance_id} in account {account_id}, region {region}...")
    response = client.terminate_instances(
        InstanceIds=[instance_id]
    )
    print(response)

    return True


def get_client(client_type, account_id, region, role=ROLE_NAME):
    other_session = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{role}",
        RoleSessionName=f"terminate_instance_{account_id}"
    )
    access_key = other_session['Credentials']['AccessKeyId']
    secret_key = other_session['Credentials']['SecretAccessKey']
    session_token = other_session['Credentials']['SessionToken']
    return boto3.client(
        client_type,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )
