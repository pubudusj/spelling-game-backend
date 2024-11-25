#!/usr/bin/env python3
import os

import aws_cdk as cdk

from config import BaseConfig
from spelling_game_backend.spelling_game_backend_stack import SpellingGameBackendStack

app = cdk.App()
base_config = BaseConfig()

SpellingGameBackendStack(app, "SpellingGameBackendStack")

app.synth()
