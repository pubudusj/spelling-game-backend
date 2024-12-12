import json
import boto3
import os

client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def lambda_handler(event, context):
    payload = json.loads(event["body"])

    # Start the Step Function execution
    response = client.start_sync_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=json.dumps(
            {"language": payload["language"], "iterate": ["1", "2", "3", "4", "5"]}
        ),
    )

    return {
        "statusCode": 200,
        "body": json.dumps(json.loads(response["output"])),
    }
