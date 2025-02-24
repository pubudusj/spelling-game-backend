"""Words backend nested stack."""

from dataclasses import dataclass
from aws_cdk import (
    CfnOutput,
    Stack,
    NestedStack,
    aws_sns as sns,
    aws_s3 as s3,
    aws_dynamodb as ddb,
)

from spelling_game_backend.constructs.words_backend_state_machine import (
    WordsBackendStateMachine,
    WordsBackendStateMachineParams,
)
from spelling_game_backend.constructs.words_backend_lambdas import (
    WordsBackendLambdaFunctions,
    WordsBackendLambdaFunctionsParams,
)
from spelling_game_backend.constructs.words_backend_api import (
    WordsBackendApi,
    WordsBackendApiParams,
)
from spelling_game_backend.constructs.backend_api_lambdas import (
    BackendApiLambdaFunctions,
    BackendApiLambdaFunctionsParams,
)


@dataclass
class WordsBackendStackParams:
    """Parameters for the WordsBackendStack."""

    dynamodb_table: ddb.Table
    s3_bucket: s3.Bucket


class WordsBackendStack(NestedStack):
    """The word backend stack."""

    def __init__(
        self, scope: Stack, construct_id: str, params: WordsBackendStackParams, **kwargs
    ) -> None:
        """Construct a new WordsBackendStack."""
        super().__init__(scope, construct_id, **kwargs)

        self.notification_sns_topic = sns.Topic(
            self,
            "WordsBackendNotificationSNS",
            display_name="WordsBackendNotificationSNS",
            topic_name="WordsBackendNotificationSNS",
        )

        self.words_backend_lambda_functions = WordsBackendLambdaFunctions(
            self,
            "WordsBackendLambdaFunctions",
            params=WordsBackendLambdaFunctionsParams(
                s3_bucket=params.s3_bucket,
                dynamodb_table=params.dynamodb_table,
            ),
        )

        self.words_backend_state_machine = WordsBackendStateMachine(
            self,
            "WordsBackendStateMachine",
            params=WordsBackendStateMachineParams(
                s3_bucket=params.s3_bucket,
                dynamodb_table=params.dynamodb_table,
                sns_topic=self.notification_sns_topic,
                presigned_url_lambda=self.words_backend_lambda_functions.presigned_url_lambda,
                get_unique_results_lambda=self.words_backend_lambda_functions.get_unique_results_lambda,
            ),
        )

        self.backend_api_lambda_functions = BackendApiLambdaFunctions(
            self,
            "BackendApiLambdaFunctions",
            params=BackendApiLambdaFunctionsParams(
                dynamodb_table=params.dynamodb_table,
                state_machine=self.words_backend_state_machine.words_backend_state_machine,
            ),
        )

        self.words_backend_api = WordsBackendApi(
            self,
            "WordsBackendApi",
            params=WordsBackendApiParams(
                state_machine=self.words_backend_state_machine.words_backend_state_machine,
                generate_questions_lambda=self.backend_api_lambda_functions.generate_questions_lambda,
                validate_answers_lambda=self.backend_api_lambda_functions.validate_answers_lambda,
                custom_authorizer=self.backend_api_lambda_functions.custom_authorizer,
            ),
        )

        CfnOutput(
            self,
            "WordsBackendApiUrl",
            value=self.words_backend_api.words_backend_api.url,
            description="Words Backend API URL",
        )
