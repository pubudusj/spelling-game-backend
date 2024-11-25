"""Spelling Game Backend Stack."""

from aws_cdk import (
    Stack,
)
from constructs import Construct

from spelling_game_backend.stacks.words_generator import WordsGeneratorStack
from spelling_game_backend.stacks.words_backend import (
    WordsBackendStack,
    WordsBackendStackParams,
)


class SpellingGameBackendStack(Stack):
    """Spellling Game Backend Stack."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.words_generator_stack = WordsGeneratorStack(self, "WordsGeneratorStack")

        self.words_backend_stack = WordsBackendStack(
            self,
            "WordsBackendStack",
            params=WordsBackendStackParams(
                s3_bucket=self.words_generator_stack.words_generator_storage.words_storage_s3_bucket,
                dynamodb_table=self.words_generator_stack.words_generator_storage.words_storage_dynamodb_table,
            ),
        )
