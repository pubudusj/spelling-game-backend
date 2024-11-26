import boto3
import os

s3_client = boto3.client("s3")
PRESIGNED_URL_EXPIRATION_SECONDS = 120
bucket_name = os.environ["BUCKET_NAME"]


def lambda_handler(event, context):
    s3_file_path = event["s3file"]["S"]
    object_key = s3_file_path.split(f"{bucket_name}/")[-1]
    expiration = event.get("expiration", PRESIGNED_URL_EXPIRATION_SECONDS)

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_key},
        ExpiresIn=expiration,
    )

    return {"url": presigned_url}
