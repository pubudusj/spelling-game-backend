import json
import boto3
import os

client = boto3.client("dynamodb")
DDB_TABLE_NAME = os.environ["DDB_TABLE_NAME"]


def lambda_handler(event, context):
    payload = json.loads(event["body"])

    # Get DynamoDB keys from inputs
    keys = [
        {
            "pk": {"S": f"Word#{payload["language"]}"},
            "sk": {"S": item["id"]},
        }
        for item in payload["answers"]
    ]

    # BatchGetItem from DynamoDB
    response = client.batch_get_item(
        RequestItems={
            f"{DDB_TABLE_NAME}": {
                "Keys": keys,
                "ProjectionExpression": "sk, word",
            },
        },
    )

    # Process the results
    results_from_db = {
        item["sk"]["S"]: item["word"]["S"]
        for item in response["Responses"][DDB_TABLE_NAME]
    }

    # Compare each input against DynamoDB data
    results = [
        {
            "id": item["id"],
            "original_word": results_from_db.get(item["id"], None),
            "correct": results_from_db.get(item["id"], "").lower()
            == item["word"].lower(),
        }
        for item in payload["answers"]
    ]

    output_headers = {
        "Access-Control-Allow-Origin": "*",  # TODO: update with the domain input
        "Access-Control-Allow-Methods": "OPTIONS, POST",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    return {
        "statusCode": 200,
        "body": json.dumps(results),
        "headers": output_headers,
    }
