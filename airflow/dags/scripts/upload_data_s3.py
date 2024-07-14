import boto3
import json
import os

# Upload JSON files to the S3 bucket 
def s3_bucket_upload(data:list, key_name:str, bucket_name:str):
    try:
        access_key = os.environ['ACCESS_KEY']
        secret_key = os.environ['SECRET_KEY']
        
        s3 = boto3.client("s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        
        data = json.dumps(data, indent=4)
        s3.put_object(
            Body=data,
            Bucket=bucket_name,
            Key=key_name
        )
    except Exception as e:
        print(f"Error uploading file to S3: {e}")