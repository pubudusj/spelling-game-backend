"""Construct for WordsBackendApi."""

import json
from dataclasses import dataclass
from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_apigateway as apigateway,
    aws_iam as iam,
)
from constructs import Construct
from config import BaseConfig


@dataclass
class WordsBackendApiParams:
    """Parameters for the WordsBackendApi."""

    state_machine: sfn.StateMachine
    generate_questions_lambda: _lambda.Function
    validate_answers_lambda: _lambda.Function
    custom_authorizer: _lambda.Function


class WordsBackendApi(Construct):
    """State machine for words backend."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params=WordsBackendApiParams,
        **kwargs,
    ) -> None:
        """Construct a new WordsBackendStateMachine."""
        super().__init__(scope=scope, id=construct_id, **kwargs)

        config = BaseConfig()

        # Create the API Gateway
        self.words_backend_api = apigateway.RestApi(
            self,
            "WordsBackendApi",
            rest_api_name="WordsBackendApi",
            description="Words Backend API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=apigateway.Cors.DEFAULT_HEADERS
                + [config.apigw_custom_header_name],
            ),
        )

        # Custom Authorizer
        self.custom_authorizer = apigateway.RequestAuthorizer(
            self,
            "LambdaHeaderAuthorizer",
            handler=params.custom_authorizer,
            identity_sources=[
                apigateway.IdentitySource.header(config.apigw_custom_header_name)
            ],
            results_cache_ttl=Duration.seconds(30),
        )

        self._build_questions_api(params)

        self._validate_answers_api(params)

    def _build_questions_api(self, params: WordsBackendApiParams):
        """Build the /questions api."""

        apigw_lambda_execution_role = iam.Role(
            self,
            "WordsApiQuestionsResourceLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Role for words api answers resource Lambda execution.",
            inline_policies={
                "LambdaExecutionPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=[params.generate_questions_lambda.function_arn],
                        ),
                    ]
                ),
            },
        )

        # Request model for /questions api
        request_model = self.words_backend_api.add_model(
            "QuestionsRequestModel",
            content_type="application/json",
            model_name="QuestionsRequestModel",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                title="QuestionsRequestSchema",
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "language": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        description="Language of the request, either en-US or nl-NL",
                        enum=["en-US", "nl-NL"],
                    ),
                },
                required=["language"],
            ),
        )

        request_validator = apigateway.RequestValidator(
            self,
            "QuestionsRequestValidator",
            rest_api=self.words_backend_api,
            validate_request_body=True,
        )

        # add method to /questions api
        self.words_backend_api.root.add_resource("questions").add_method(
            "POST",
            apigateway.LambdaIntegration(
                params.generate_questions_lambda,
                proxy=True,
                credentials_role=apigw_lambda_execution_role,
            ),
            request_models={"application/json": request_model},
            method_responses=[apigateway.MethodResponse(status_code="200")],
            request_validator=request_validator,
            authorization_type=apigateway.AuthorizationType.CUSTOM,
            authorizer=self.custom_authorizer,
        )

    def _validate_answers_api(self, params: WordsBackendApiParams):
        """Build the /answers api."""

        apigw_lambda_execution_role = iam.Role(
            self,
            "WordsApiAnswersResourceLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Role for words api answers resource Lambda execution.",
            inline_policies={
                "LambdaExecutionPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=[params.validate_answers_lambda.function_arn],
                        ),
                    ]
                ),
            },
        )

        # Request model for /answers api
        request_model = self.words_backend_api.add_model(
            "CheckAnswersRequestModel",
            content_type="application/json",
            model_name="CheckAnswersRequestModel",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                title="CheckAnswersRequestSchema",
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "language": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        description="Language of the request, either en-US or nl-NL",
                        enum=["en-US", "nl-NL"],
                    ),
                    "answers": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.ARRAY,
                        items=apigateway.JsonSchema(
                            type=apigateway.JsonSchemaType.OBJECT,
                            properties={
                                "id": apigateway.JsonSchema(
                                    type=apigateway.JsonSchemaType.STRING,
                                    description="Validate md5 hash",
                                    pattern="^[0-9a-f]{32}$",
                                ),
                                "word": apigateway.JsonSchema(
                                    type=apigateway.JsonSchemaType.STRING,
                                    description="Word to validate as answer",
                                    min_length=0,
                                    max_length=20,
                                ),
                            },
                            required=["id", "word"],
                        ),
                    ),
                },
                required=["language", "answers"],
            ),
        )

        request_validator = apigateway.RequestValidator(
            self,
            "CheckAnswersRequestValidator",
            rest_api=self.words_backend_api,
            validate_request_body=True,
        )

        # add method to /answers api
        self.words_backend_api.root.add_resource("answers").add_method(
            "POST",
            apigateway.LambdaIntegration(
                params.validate_answers_lambda,
                proxy=True,
                credentials_role=apigw_lambda_execution_role,
            ),
            request_models={"application/json": request_model},
            method_responses=[apigateway.MethodResponse(status_code="200")],
            request_validator=request_validator,
            authorization_type=apigateway.AuthorizationType.CUSTOM,
            authorizer=self.custom_authorizer,
        )
