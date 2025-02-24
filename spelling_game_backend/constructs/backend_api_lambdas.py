"""Construct for WordsBackendLambdaFunctions."""

from dataclasses import dataclass
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_dynamodb as ddb,
    aws_stepfunctions as sfn,
    aws_ssm as ssm,
)
from constructs import Construct
from config import BaseConfig


@dataclass
class BackendApiLambdaFunctionsParams:
    """Parameters for the BackendApiLambdaFunctions."""

    dynamodb_table: ddb.Table
    state_machine: sfn.StateMachine


class BackendApiLambdaFunctions(Construct):
    """Lambda functions for backend api."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params=BackendApiLambdaFunctionsParams,
        **kwargs,
    ) -> None:
        """Construct a new BackendApiLambdaFunctions."""
        super().__init__(scope=scope, id=construct_id, **kwargs)

        config = BaseConfig()

        # Import ssm parameter
        self.apigw_custom_header_parameter = (
            ssm.StringParameter.from_secure_string_parameter_attributes(
                self,
                "APIGWCustomHeaderSecureParameter",
                parameter_name=config.apigw_custom_header_ssm_parameter,
            )
        )

        # Create generate questions Lambda function
        self.generate_questions_lambda = _lambda.Function(
            self,
            "GenerateQuestions",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "spelling_game_backend/lambda/generate_questions"
            ),
            timeout=Duration.seconds(2),
            environment={
                "STATE_MACHINE_ARN": params.state_machine.state_machine_arn,
            },
        )

        self.generate_questions_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["states:StartSyncExecution"],
                resources=[params.state_machine.state_machine_arn],
            )
        )

        # Create validate answers Lambda function
        self.validate_answers_lambda = _lambda.Function(
            self,
            "ValidateAnswers",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "spelling_game_backend/lambda/validate_answers"
            ),
            timeout=Duration.seconds(2),
            environment={
                "DDB_TABLE_NAME": params.dynamodb_table.table_name,
            },
        )

        self.validate_answers_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["dynamodb:BatchGetItem"],
                resources=[params.dynamodb_table.table_arn],
            )
        )

        # Custom authorizer lambda function
        self.custom_authorizer = _lambda.Function(
            self,
            "BackendLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "spelling_game_backend/lambda/custom_authorizer"
            ),
            timeout=Duration.seconds(2),
            environment={
                "SSM_PARAMETER_NAME": self.apigw_custom_header_parameter.parameter_name,
                "CUSTOM_HEADER_KEY": config.apigw_custom_header_name,
            },
        )

        self.custom_authorizer.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[self.apigw_custom_header_parameter.parameter_arn],
            )
        )
