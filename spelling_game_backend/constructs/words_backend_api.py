"""Construct for WordsBackendApi."""

import json
from dataclasses import dataclass
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_apigateway as apigateway,
    aws_iam as iam,
)
from constructs import Construct


@dataclass
class WordsBackendApiParams:
    """Parameters for the WordsBackendApi."""

    state_machine: sfn.StateMachine
    validate_answers_lambda: _lambda.Function


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

        # Create the API Gateway
        self.words_backend_api = apigateway.RestApi(
            self,
            "WordsBackendApi",
            rest_api_name="WordsBackendApi",
            description="Words Backend API",
        )

        self._build_questions_api(params)

        self._validate_answers_api(params)

    def _build_questions_api(self, params: WordsBackendApiParams):
        """Build the /questions api."""

        apigw_sf_execution_role = iam.Role(
            self,
            "WordsApiSFExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Role for words api SF execution.",
            inline_policies={
                "StepFunctionExecutionPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["states:StartSyncExecution"],
                            resources=[params.state_machine.state_machine_arn],
                        ),
                    ]
                ),
            },
        )

        integration_options = apigateway.IntegrationOptions(
            credentials_role=apigw_sf_execution_role,
            request_parameters={
                "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
            },
            passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
            request_templates={
                "application/json": f"""
                        #set($language = $input.json('$.language'))
                        {{
                            "stateMachineArn": "{params.state_machine.state_machine_arn}",
                            "input": "{{\\"language\\":$util.escapeJavaScript($language),\\"iterate\\":[1,2,3,4,5]}}"
                        }}
                    """
            },
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": '#set($inputRoot = $util.parseJson($input.path(\'$.output\')))[#foreach($elem in $inputRoot){"id":"$elem.id","language":"$elem.language","description":"$elem.description","character_count":$elem.charcount,"audio_url":"$elem.url"}#if($foreach.hasNext),#end#end]'
                    },
                )
            ],
        )

        # Request model for /questions api
        request_model = self.words_backend_api.add_model(
            "QuestionsRequestModel",
            content_type="application/json",
            model_name="QuestionsRequestModel",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                title="GetQuestionsRequest",
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "language": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        description="Language of the questions",
                        enum=["en-US", "nl-NL"],
                    ),
                },
                required=["language"],
            ),
        )

        # Request validator with body validation
        request_validator = apigateway.RequestValidator(
            self,
            "QuestionsRequestValidator",
            rest_api=self.words_backend_api,
            validate_request_body=True,
        )

        # add method to /questions api
        self.words_backend_api.root.add_resource("questions").add_method(
            "POST",
            apigateway.AwsIntegration(
                service="states",
                action="StartSyncExecution",
                integration_http_method="POST",
                options=integration_options,
            ),
            request_models={"application/json": request_model},
            method_responses=[apigateway.MethodResponse(status_code="200")],
            request_validator=request_validator,
        )

    def _validate_answers_api(self, params: WordsBackendApiParams):
        """Build the /answers api."""

        apigw_lambda_execution_role = iam.Role(
            self,
            "WordsApiLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Role for words api Lambda execution.",
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
                                    description="Unique identifier in UUID format",
                                    pattern="^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
                                ),
                                "word": apigateway.JsonSchema(
                                    type=apigateway.JsonSchemaType.STRING,
                                    description="Word to validate as answer",
                                    min_length=1,
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
        )
