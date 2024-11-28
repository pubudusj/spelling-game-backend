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


@dataclass
class WordsBackendApiParams:
    """Parameters for the WordsBackendApi."""

    state_machine: sfn.StateMachine


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

        apigw_role = iam.Role(
            self,
            "WordsApiExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Role for words api.",
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
            credentials_role=apigw_role,
            request_parameters={
                "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
            },
            passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
            request_templates={
                "application/json": json.dumps(
                    {
                        "stateMachineArn": f"{params.state_machine.state_machine_arn}",
                        "input": '{"language":"en-US","iterate":[1,2,3,4,5]}',
                    }
                )
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
        # add method to /words api
        apigw_method = self.words_backend_api.root.add_resource("words").add_method(
            "POST",
            apigateway.AwsIntegration(
                service="states",
                action="StartSyncExecution",
                integration_http_method="POST",
                options=integration_options,
            ),
            method_responses=[apigateway.MethodResponse(status_code="200")],
        )
