"""Construct for WordsGeneratorStorage."""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class WordsGeneratorStorage(Construct):
    """Storage for Words."""

    def __init__(self, scope: Stack, construct_id: str, **kwargs) -> None:
        """Construct a new WordsGeneratorStorage."""
        super().__init__(
            scope=scope,
            id=construct_id,
            **kwargs,
        )

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
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=2,
        )
