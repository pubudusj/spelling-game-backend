"""Words backend nested stack."""

from dataclasses import dataclass
from aws_cdk import (
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

        self.words_backend_state_machine = WordsBackendStateMachine(
            self,
            "WordsBackendStateMachine",
            params=WordsBackendStateMachineParams(
                s3_bucket=params.s3_bucket,
                dynamodb_table=params.dynamodb_table,
                sns_topic=self.notification_sns_topic,
            ),
        )
