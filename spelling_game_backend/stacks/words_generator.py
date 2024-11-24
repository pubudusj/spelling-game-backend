"""Words generator nested stack."""

from aws_cdk import (
    Stack,
    NestedStack,
    aws_sns as sns,
)

from spelling_game_backend.constructs.words_generator_storage import (
    WordsGeneratorStorage,
)
from spelling_game_backend.constructs.words_generator_state_machine import (
    WordsGeneratorStateMachine,
    WordsGeneratorStateMachineParams,
)
from spelling_game_backend.constructs.words_generator_scheduler import (
    WordsGeneratorScheduler,
    WordsGeneratorSchedulerParams,
)


class WordsGeneratorStack(NestedStack):
    """The word generator stack."""

    def __init__(self, scope: Stack, construct_id: str, **kwargs) -> None:
        """Construct a new WordsGeneratorStack."""
        super().__init__(scope, construct_id, **kwargs)

        self.notification_sns = sns.Topic(
            self,
            "WordsGeneratorNotificationSNS",
            display_name="WordsGeneratorNotificationSNS",
            topic_name="WordsGeneratorNotificationSNS",
        )

        self.words_generator_storage = WordsGeneratorStorage(
            self, "WordsGeneratorStorage"
        )

        self.words_generator_state_machine = WordsGeneratorStateMachine(
            self,
            "WordsGeneratorStateMachine",
            params=WordsGeneratorStateMachineParams(
                s3_bucket=self.words_generator_storage.words_storage_s3_bucket,
                dynamodb_table=self.words_generator_storage.words_storage_dynamodb_table,
                sns_topic=self.notification_sns,
            ),
        )

        self.words_generator_scheduler = WordsGeneratorScheduler(
            self,
            "WordsGeneratorScheduler",
            params=WordsGeneratorSchedulerParams(
                state_machine=self.words_generator_state_machine.word_generator_state_machine,
            ),
        )
