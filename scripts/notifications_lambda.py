import boto3
import json


sns_topic_arn = ""
email_subject = "Failure Alert: Data scraping function failed!"

# Sends a notification when the lambda function fails
def lambda_handler(event, context):
    sns = boto3.client("sns")
    sns.publish(
        TargetArn=sns_topic_arn,
        Message=json.dumps(event),
        Subject=email_subject,
    )