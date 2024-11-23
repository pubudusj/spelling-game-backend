"""The GenerateWordsStack module."""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_sns as sns,
)

from constructs import Construct

from generate_words.stacks.storage import StorageStack
from generate_words.stacks.state_machine import (
    GenerateWordsStateMachineStack,
    GenerateWordsStateMachineStackParams,
)
from generate_words.stacks.scheduler import SchedulerStack, SchedulerStackParams


class GenerateWordsStack(Stack):  # pylint: disable=too-many-instance-attributes
    """GenerateWordsStack stack."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Construct a new GenerateWordsStack."""
        super().__init__(scope, construct_id, **kwargs)

        self.notification_sns = sns.Topic(
            self,
            "GenerateWordsNotificationSNS",
            display_name="GenerateWordsNotificationSNS",
            topic_name="GenerateWordsNotification",
        )

        self.storage_stack = StorageStack(self, "StorageStack")

        self.generate_words_state_machine_stack = GenerateWordsStateMachineStack(
            self,
            "GenerateWordsStateMachineStack",
            params=GenerateWordsStateMachineStackParams(
                words_s3_bucket=self.storage_stack.words_storage_s3_bucket,
                dynamodb_table=self.storage_stack.words_storage_dynamodb_table,
                notification_sns=self.notification_sns,
            ),
        )

        self.scheduler_stack = SchedulerStack(
            self,
            "SchedulerStack",
            params=SchedulerStackParams(
                state_machine=self.generate_words_state_machine_stack.word_generator_state_machine,
            ),
        )
