"""Construct for WordsBackendLambdaFunctions."""

from dataclasses import dataclass
from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct


@dataclass
class WordsBackendLambdaFunctionsParams:
    """Parameters for the WordsBackendLambdaFunctions."""

    s3_bucket: s3.Bucket


class WordsBackendLambdaFunctions(Construct):
    """State machine for words backend."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params=WordsBackendLambdaFunctionsParams,
        **kwargs,
    ) -> None:
        """Construct a new WordsBackendStateMachine."""
        super().__init__(scope=scope, id=construct_id, **kwargs)

        self.presigned_url_lambda = _lambda.Function(
            self,
            "CreatePresignedURL",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "spelling_game_backend/lambda/create_presigned_url"
            ),
            environment={"BUCKET_NAME": params.s3_bucket.bucket_name},
            timeout=Duration.seconds(3),
        )

        self.presigned_url_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                resources=[params.s3_bucket.bucket_arn + "/*"],
            )
        )

        self.get_unique_results_lambda = _lambda.Function(
            self,
            "GetUniqueResults",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "spelling_game_backend/lambda/get_unique_results"
            ),
            timeout=Duration.seconds(2),
        )
