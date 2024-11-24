"""Spelling Game Backend Stack."""

from aws_cdk import (
    Stack,
)
from constructs import Construct

from spelling_game_backend.stacks.words_generator import WordsGeneratorStack


class SpellingGameBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.word_generator_stack = WordsGeneratorStack(self, "WordsGeneratorStack")
