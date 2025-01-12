"""Construct for WordsGeneratorStateMachine."""

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
class WordsGeneratorStateMachineParams:
    """Parameters for the WordsGeneratorStateMachine."""

    s3_bucket: s3.Bucket
    dynamodb_table: ddb.Table
    sns_topic: sns.Topic


class WordsGeneratorStateMachine(Construct):
    """State machine for words generation."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params=WordsGeneratorStateMachineParams,
        **kwargs,
    ) -> None:
        """Construct a new WordsGeneratorStateMachine."""
        super().__init__(scope=scope, id=construct_id, **kwargs)

        model = bedrock.FoundationModel.from_foundation_model_id(
            self,
            "BedrockModelAnthropicClaude35Haiku",
            bedrock.FoundationModelIdentifier.ANTHROPIC_CLAUDE_3_HAIKU_20240307_V1_0,
        )
        prompt = "Generate 5 unique words that has random number of characters more than 4 and less than 10 in {} language. For each word, provide a brief description of its meaning in English with more than a couple of words. Produce output only in minified JSON array with the keys word and description."
        call_bedrock_task = tasks.BedrockInvokeModel(
            self,
            "GenerateWords",
            model=model,
            body=sfn.TaskInput.from_object(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": sfn.JsonPath.format(
                                        prompt, sfn.JsonPath.string_at("$.languageName")
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ),
            result_selector={
                "words": sfn.JsonPath.string_to_json(
                    sfn.JsonPath.string_at("$.Body.content[0].text")
                )
            },
        )

        langages_map = sfn.Map(
            self,
            "LanguagesMap",
            items_path="$.words",
            item_selector={
                "language": sfn.JsonPath.string_at("$$.Execution.Input.language"),
                "word": sfn.JsonPath.string_at("$$.Map.Item.Value.word"),
                "description": sfn.JsonPath.string_at("$$.Map.Item.Value.description"),
            },
        )

        synthesis_task_status_choice = sfn.Choice(
            self,
            "SynthesisTaskStatusChoice",
        )

        save_word_to_dynamodb = tasks.DynamoPutItem(
            self,
            "SaveWordToDynamoDB",
            table=params.dynamodb_table,
            item={
                "pk": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.format("Word#{}", sfn.JsonPath.string_at("$.language"))
                ),
                "sk": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("States.Hash($.word, 'MD5')")
                ),
                "word": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$.word")
                ),
                "description": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$.description")
                ),
                "s3file": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$.output.SynthesisTask.OutputUri")
                ),
                "charcount": tasks.DynamoAttributeValue.number_from_string(
                    sfn.JsonPath.format(
                        "{}",
                        sfn.JsonPath.string_at(
                            "$.output.SynthesisTask.RequestCharacters"
                        ),
                    )
                ),
                "updated_at": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$$.State.EnteredTime")
                ),
            },
        )

        get_speech_synthesis_task = tasks.CallAwsService(
            self,
            "GetSpeechSynthesisTaskStatus",
            service="polly",
            action="getSpeechSynthesisTask",
            parameters={
                "TaskId": sfn.JsonPath.string_at("$.output.SynthesisTask.TaskId"),
            },
            iam_resources=["*"],
            result_path="$.output",
        ).next(synthesis_task_status_choice)

        failed_sns_notification = tasks.SnsPublish(
            self,
            "FailedNotificationToSNS",
            topic=params.sns_topic,
            message=sfn.TaskInput.from_object(
                {
                    "output": sfn.JsonPath.object_at("$.output"),
                }
            ),
        )

        synthesis_task_status_choice.when(
            sfn.Condition.string_equals(
                "$.output.SynthesisTask.TaskStatus", "completed"
            ),
            save_word_to_dynamodb,
        ).when(
            sfn.Condition.string_equals("$.output.SynthesisTask.TaskStatus", "failed"),
            failed_sns_notification,
        ).otherwise(
            sfn.Wait(
                self,
                "WaitForSynthesisTaskStatus",
                time=sfn.WaitTime.duration(Duration.seconds(5)),
            ).next(get_speech_synthesis_task)
        )

        speech_synthesis_task_nl = tasks.CallAwsService(
            self,
            "StartSpeechSynthesisTaskNL",
            service="polly",
            action="startSpeechSynthesisTask",
            parameters={
                "Engine": "standard",
                "LanguageCode": "nl-NL",
                "OutputFormat": "mp3",
                "OutputS3BucketName": params.s3_bucket.bucket_name,
                "OutputS3KeyPrefix": "nl-NL/",
                "Text": sfn.JsonPath.string_at("$.word"),
                "VoiceId": "Ruben",
            },
            iam_resources=["*"],
            result_path="$.output",
        ).next(get_speech_synthesis_task)

        speech_synthesis_task_en = tasks.CallAwsService(
            self,
            "StartSpeechSynthesisTaskEN",
            service="polly",
            action="startSpeechSynthesisTask",
            parameters={
                "Engine": "standard",
                "LanguageCode": "en-US",
                "OutputFormat": "mp3",
                "OutputS3BucketName": params.s3_bucket.bucket_name,
                "OutputS3KeyPrefix": "en-US/",
                "Text": sfn.JsonPath.string_at("$.word"),
                "VoiceId": "Matthew",
            },
            iam_resources=["*"],
            result_path="$.output",
        ).next(get_speech_synthesis_task)

        language_choice = (
            sfn.Choice(
                self,
                "LanguageChoice",
            )
            .when(
                sfn.Condition.string_equals("$.language", "nl-NL"),
                speech_synthesis_task_nl,
            )
            .otherwise(speech_synthesis_task_en)
        )

        langages_map.item_processor(language_choice)

        self.word_generator_state_machine = sfn.StateMachine(
            self,
            "WordGeneratorStateMachine",
            state_machine_type=sfn.StateMachineType.STANDARD,
            definition_body=sfn.DefinitionBody.from_chainable(
                sfn.Pass(
                    self,
                    "Start statemachine",
                )
                .next(call_bedrock_task)
                .next(langages_map)
            ),
        )

        self.word_generator_state_machine.role.attach_inline_policy(
            iam.Policy(
                self,
                "StateMachineExecutionPolicy",
                document=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "polly:StartSpeechSynthesisTask",
                                "polly:GetSpeechSynthesisTask",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["s3:PutObject"],
                            resources=[
                                f"arn:aws:s3:::{params.s3_bucket.bucket_name}",
                                f"arn:aws:s3:::{params.s3_bucket.bucket_name}/*",
                            ],
                        ),
                    ]
                ),
            )
        )
