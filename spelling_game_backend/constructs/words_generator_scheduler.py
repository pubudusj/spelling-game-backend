"""Construct for WordsGeneratorScheduler."""

import json

from dataclasses import dataclass
from aws_cdk import (
    Stack,
    aws_scheduler as scheduler,
    aws_iam as iam,
    aws_stepfunctions as sfn,
)
from constructs import Construct


@dataclass
class WordsGeneratorSchedulerParams:
    """Parameters for the WordsGeneratorScheduler."""

    state_machine: sfn.StateMachine


class WordsGeneratorScheduler(Construct):
    """Schedules for words generation."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params=WordsGeneratorSchedulerParams,
        **kwargs,
    ) -> None:
        """Construct a new WordsGeneratorSchedule."""
        super().__init__(scope=scope, id=construct_id, **kwargs)

        # NL words generator state machine
        scheduler_role = iam.Role(
            self,
            "WordsGenerateSchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
            inline_policies={
                "StepFunctionExecutionPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["states:StartExecution"],
                            effect=iam.Effect.ALLOW,
                            resources=[params.state_machine.state_machine_arn],
                        )
                    ]
                )
            },
        )

        self.scheduler_nl = scheduler.CfnSchedule(
            self,
            "WordsGeneratorSchedulerNL",
            schedule_expression="cron(*/2 * * * ? *)",
            target=scheduler.CfnSchedule.TargetProperty(
                arn=params.state_machine.state_machine_arn,
                role_arn=scheduler_role.role_arn,
                input=json.dumps(
                    {
                        "language": "nl-NL",
                        "languageName": "Dutch",
                    }
                ),
            ),
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="FLEXIBLE",
                maximum_window_in_minutes=1,
            ),
            state="ENABLED",
        )

        self.scheduler_en = scheduler.CfnSchedule(
            self,
            "WordsGeneratorSchedulerEN",
            schedule_expression="cron(*/2 * * * ? *)",
            target=scheduler.CfnSchedule.TargetProperty(
                arn=params.state_machine.state_machine_arn,
                role_arn=scheduler_role.role_arn,
                input=json.dumps(
                    {
                        "language": "en-US",
                        "languageName": "English",
                    }
                ),
            ),
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="FLEXIBLE",
                maximum_window_in_minutes=1,
            ),
            state="ENABLED",
        )
