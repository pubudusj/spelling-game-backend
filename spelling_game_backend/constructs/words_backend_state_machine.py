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

        # Define the state machine
        sfn.StateMachine(
            self,
            "WordsBackendStateMachine",
            state_machine_type=sfn.StateMachineType.STANDARD,
            definition_body=self._create_state_machine_definition(params),
            timeout=Duration.minutes(5),
        )

    def _create_state_machine_definition(self, params: WordsBackendStateMachineParams):
        """Create the state machine definition."""

        ddb_scan = tasks.CallAwsService(
            self,
            "DynamoDBGetSingleItem",
            service="dynamodb",
            action="scan",
            parameters={
                "TableName": params.dynamodb_table.table_arn,
                "Limit": 1,
                "ExclusiveStartKey": {
                    "pk": {
                        "S": sfn.JsonPath.format(
                            "Word#{}",
                            sfn.JsonPath.string_at("$$.Execution.Input.language"),
                        ),
                    },
                    "sk": {"S": sfn.JsonPath.string_at("States.UUID()")},
                },
                "ReturnConsumedCapacity": "TOTAL",
            },
            result_selector={
                "itemcount": sfn.JsonPath.number_at("States.ArrayLength($.Items)"),
                "items": sfn.JsonPath.string_at("$.Items"),
            },
            iam_resources=[params.dynamodb_table.table_arn],
        )

        check_item_count = (
            sfn.Choice(
                self,
                "CheckItemCount",
                output_path=sfn.JsonPath.string_at("$.items[0]"),
            )
            .when(
                sfn.Condition.number_greater_than("$.itemcount", 0),
                sfn.Pass(self, "GeneratePresignedURL"),
            )
            .otherwise(
                sfn.Pass(
                    self,
                    "DDBScanFailed",
                )
            )
        )

        return sfn.DefinitionBody.from_chainable(
            sfn.Pass(
                self,
                "Start statemachine",
            )
            .next(ddb_scan)
            .next(check_item_count)
        )
