import json
import boto3
import os

client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def lambda_handler(event, context):
    payload = json.loads(event["body"])
    output_headers = {
        "Access-Control-Allow-Origin": "*",  # TODO: update with the domain input
        "Access-Control-Allow-Methods": "OPTIONS, POST",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    try:
        # Start the Step Function execution
        response = client.start_sync_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(
                {"language": payload["language"], "iterate": ["1", "2", "3", "4", "5"]}
            ),
        )

        questions = json.loads(response["output"])
        for item in questions:
            if "charcount" in item:
                item["charcount"] = int(item["charcount"])
            if "description" in item:
                item["description"] = item["description"].strip().capitalize()

        return {
            "statusCode": 200,
            "body": json.dumps({"questions": questions}),
            "headers": output_headers,
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Something went wrong", "error": str(e)}),
            "headers": output_headers,
        }
