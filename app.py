#!/usr/bin/env python3
import os

import aws_cdk as cdk

# from spelling_game_backend.spelling_game_backend_stack import SpellingGameBackendStack
from generate_words.generate_words_stack import GenerateWordsStack

app = cdk.App()

GenerateWordsStack(app, "GenerateWordsStack")
app.synth()
