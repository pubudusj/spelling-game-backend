"""Hosting resources nested stack."""

from dataclasses import dataclass
from aws_cdk import (
    Duration,
    Stack,
    NestedStack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_ssm as ssm,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigateway,
)
from config import BaseConfig


@dataclass
class HostingResourcesStackParams:
    """Parameters for the WordsBackendStack."""

    rest_api: apigateway.RestApi
    ssm_parameter: ssm.StringParameter


class HostingResourcesStack(NestedStack):
    """The hosting resources stack."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params: HostingResourcesStackParams,
        **kwargs
    ) -> None:
        """Construct a new HostingResourcesStack."""
        super().__init__(scope, construct_id, **kwargs)

        config = BaseConfig()
        apigw_custom_header_key = config.apigw_custom_header_name

        self.hosting_s3_bucket = s3.Bucket(
            self,
            "WordGameFrontendHostingBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # Create a cloudfront distribution to host the frontend
        self.cloudfront_distribution = cloudfront.Distribution(
            self,
            "WordGameFrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.hosting_s3_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_page_path="/index.html",
                    response_http_status=200,
                )
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_200,
        )

        # Update cloudfront distribution with the custom header
        update_secure_header = _lambda.Function(
            self,
            "UpdateSecureHeaderFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "spelling_game_backend/lambda/apigw_update_custom_header"
            ),
            timeout=Duration.seconds(5),
            environment={
                "SSM_PARAMETER_NAME": params.ssm_parameter.parameter_name,
                "CLOUDFRONT_DISTRIBUTION_ID": self.cloudfront_distribution.distribution_id,
                "APIGATEWAY_URL": params.rest_api.url,
                "CUSTOM_HEADER_KEY": apigw_custom_header_key,
            },
        )

        update_secure_header.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:PutParameter"],
                resources=[params.ssm_parameter.parameter_arn],
            )
        )

        update_secure_header.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudfront:GetDistributionConfig",
                    "cloudfront:UpdateDistribution",
                ],
                resources=[self.cloudfront_distribution.distribution_arn],
            )
        )
