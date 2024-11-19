import aws_cdk as core
import aws_cdk.assertions as assertions

from spelling_game_backend.spelling_game_backend_stack import SpellingGameBackendStack

# example tests. To run these tests, uncomment this file along with the example
# resource in spelling_game_backend/spelling_game_backend_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SpellingGameBackendStack(app, "spelling-game-backend")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
