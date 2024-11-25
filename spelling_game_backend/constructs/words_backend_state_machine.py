"""Construct for WordsBackendStateMachine."""

from dataclasses import dataclass
from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_sns as sns,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_dynamodb as ddb,
)
from constructs import Construct


@dataclass
class WordsBackendStateMachineParams:
    """Parameters for the WordsBackendStateMachine."""

    s3_bucket: s3.Bucket
    dynamodb_table: ddb.Table
    sns_topic: sns.Topic


class WordsBackendStateMachine(Construct):
    """State machine for words backend."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params=WordsBackendStateMachineParams,
        **kwargs,
    ) -> None:
        """Construct a new WordsBackendStateMachine."""
        super().__init__(scope=scope, id=construct_id, **kwargs)
