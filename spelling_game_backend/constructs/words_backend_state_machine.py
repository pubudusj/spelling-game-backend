"""Construct for WordsBackendStateMachine."""

from dataclasses import dataclass
from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_sns as sns,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_logs as logs,
    aws_dynamodb as ddb,
    aws_lambda as _lambda,
)
from constructs import Construct


@dataclass
class WordsBackendStateMachineParams:
    """Parameters for the WordsBackendStateMachine."""

    s3_bucket: s3.Bucket
    dynamodb_table: ddb.Table
    sns_topic: sns.Topic
    presigned_url_lambda: _lambda.Function
    get_unique_results_lambda: _lambda.Function


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

        words_backend_state_machine_log_group = logs.LogGroup(
            self, "WordsBackendStateMachineLogGroup"
        )

        # Define the state machine
        self.words_backend_state_machine = sfn.StateMachine(
            self,
            "WordsBackendStateMachine",
            state_machine_type=sfn.StateMachineType.EXPRESS,
            definition_body=self._create_state_machine_definition(params),
            timeout=Duration.minutes(1),
            logs=sfn.LogOptions(
                destination=words_backend_state_machine_log_group,
                level=sfn.LogLevel.ALL,
            ),
        )

    def _create_state_machine_definition(self, params: WordsBackendStateMachineParams):
        """Create the state machine definition."""

        send_sns_notification = tasks.SnsPublish(
            self,
            "FailedNotificationToSNS",
            topic=params.sns_topic,
            message=sfn.TaskInput.from_object(
                {
                    "output": sfn.JsonPath.object_at("$"),
                }
            ),
            result_selector={"error": True},
        )

        ddb_scan = tasks.CallAwsService(
            self,
            "DynamoDBGetRandomItems",
            service="dynamodb",
            action="scan",
            parameters={
                "TableName": params.dynamodb_table.table_arn,
                "Limit": 50,
                "ExclusiveStartKey": {
                    "pk": {
                        "S": sfn.JsonPath.format(
                            "Word#{}",
                            sfn.JsonPath.string_at("$$.Execution.Input.language"),
                        ),
                    },
                    "sk": {"S": sfn.JsonPath.string_at("States.UUID()")},
                },
                "FilterExpression": "pk = :pk",
                "ExpressionAttributeValues": {
                    ":pk": {
                        "S": sfn.JsonPath.format(
                            "Word#{}",
                            sfn.JsonPath.string_at("$$.Execution.Input.language"),
                        )
                    }
                },
                "ReturnConsumedCapacity": "TOTAL",
            },
            result_selector={
                "itemcount": sfn.JsonPath.number_at("States.ArrayLength($.Items)"),
                "items": sfn.JsonPath.string_at("$.Items"),
            },
            iam_resources=[params.dynamodb_table.table_arn],
        ).add_catch(send_sns_notification)

        generate_presigned_url_function_and_trasnform = tasks.LambdaInvoke(
            self,
            "GeneratePresignedURLLambdaAndTransform",
            lambda_function=params.presigned_url_lambda,
            payload=sfn.TaskInput.from_json_path_at("$"),
            output_path="$.Payload",
        )

        choose_random_item = sfn.Pass(
            self,
            "ChooseRandomItem",
            parameters={
                "item": sfn.JsonPath.object_at(
                    "States.ArrayGetItem($.items,States.MathRandom(0, States.ArrayLength($.items)))"
                ),
            },
        ).next(generate_presigned_url_function_and_trasnform)

        check_item_count = (
            sfn.Choice(
                self,
                "CheckItemCount",
            )
            .when(
                sfn.Condition.number_greater_than("$.itemcount", 0),
                choose_random_item,
            )
            .otherwise(send_sns_notification)
        )

        ddb_scan.next(check_item_count)

        get_uniq_results_lambda = tasks.LambdaInvoke(
            self,
            "GetUniqueResultsLambda",
            lambda_function=params.get_unique_results_lambda,
            payload=sfn.TaskInput.from_json_path_at("$"),
            output_path="$.Payload",
        )

        fetch_questions_map = (
            sfn.Map(
                self,
                "FetchQuestionsMap",
                items_path="$.iterate",
            )
            .item_processor(ddb_scan)
            .next(get_uniq_results_lambda)
        )

        return sfn.DefinitionBody.from_chainable(fetch_questions_map)
