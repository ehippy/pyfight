import json


def incoming_slack_webhook(event, context):

    print(event)

    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": "{\"text\": \"It's INFIGHTIN' TIME\"}"
    }

    return response
