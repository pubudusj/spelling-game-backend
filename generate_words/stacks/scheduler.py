"""Storage stack to manage scheduler related resources."""

import json

from dataclasses import dataclass
from aws_cdk import (
    Stack,
    NestedStack,
    aws_scheduler as scheduler,
    aws_iam as iam,
    aws_stepfunctions as sfn,
)


@dataclass
class SchedulerStackParams:
    """Parameters for the SchedulerStackParams."""

    state_machine: sfn.StateMachine


class SchedulerStack(NestedStack):
    """The scheduler nested stack."""

    def __init__(
        self,
        scope: Stack,
        construct_id: str,
        params: SchedulerStackParams,
        **kwargs,
    ) -> None:
        """Construct a new StorageStack."""
        super().__init__(scope, construct_id, **kwargs)

        # NL words generator state machine
        scheduler_role = iam.Role(
            self,
            "WordGenerateSchedulerRole",
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
            "SchedulerNL",
            schedule_expression="cron(*/5 * * * ? *)",
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
                maximum_window_in_minutes=3,
            ),
            state="DISABLED",
        )

        self.scheduler_en = scheduler.CfnSchedule(
            self,
            "SchedulerEN",
            schedule_expression="cron(*/5 * * * ? *)",
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
                maximum_window_in_minutes=2,
            ),
            state="DISABLED",
        )
