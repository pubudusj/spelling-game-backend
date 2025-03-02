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
    custom_resources as cr,
)
import aws_cdk.aws_scheduler_alpha as scheduler
import aws_cdk.aws_scheduler_targets_alpha as targets
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
        **kwargs,
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
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
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

        self.cloudfront_distribution.add_behavior(
            path_pattern="/prod/*",
            origin=origins.RestApiOrigin(
                params.rest_api,
                custom_headers={
                    f"{apigw_custom_header_key}": "abc123",  # This will be rotated as soon as the stack is deployed
                },
                origin_path="/",
            ),
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
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

        # AWS EventBridge scheduler to update the secure header every 24 hours
        scheduler_role = iam.Role(
            self,
            "SchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )

        scheduler_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[update_secure_header.function_arn],
            )
        )

        scheduler.Schedule(
            self,
            "Schedule",
            schedule=scheduler.ScheduleExpression.rate(Duration.hours(6)),
            target=targets.LambdaInvoke(update_secure_header, role=scheduler_role),
            description="Schedule to trigger update header lambda function every 6 hours.",
        )

        # IAM Role for custom resource
        custom_resource_role = iam.Role(
            scope=self,
            id="CustomResourceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        custom_resource_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[update_secure_header.function_arn],
            )
        )

        # Custom resource to update the secure header on stack create
        cr.AwsCustomResource(
            self,
            "UpdateSecureHeaderOnCreateCustomResource",
            on_create=cr.AwsSdkCall(
                service="lambda",
                action="Invoke",
                physical_resource_id=cr.PhysicalResourceId.of(
                    "UpdateSecureHeaderOnCreateCustomResource"
                ),
                parameters={
                    "FunctionName": update_secure_header.function_name,
                    "InvocationType": "Event",
                    "Payload": '{"RequestType": "Create"}',
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
            role=custom_resource_role,
        )
