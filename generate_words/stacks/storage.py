"""Storage stack to manage storage related resources."""

from aws_cdk import (
    Stack,
    NestedStack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)


class StorageStack(NestedStack):
    """The Storage nested stack."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        **kwargs,
    ) -> None:
        """Construct a new StorageStack."""
        super().__init__(scope, construct_id, **kwargs)

        # s3 bucket to store the word mp3 files
        self.words_storage_s3_bucket = s3.Bucket(
            self,
            "WordsStorageS3Bucket",
        )

        # dynamodb table to store the words
        self.words_storage_dynamodb_table = dynamodb.Table(
            self,
            "WordsStorageDynamoDBTable",
            partition_key=dynamodb.Attribute(
                name="pk",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="sk",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )
