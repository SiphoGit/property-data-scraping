import boto3
import logging


def s3_bucket_upload(file_path:str, key_name:str, bucket_name:str):
    logging.info(f"Uploading data to Amazon S3...") 
    
    # Upload JSON data to the S3 bucket 
    try:
        s3 = boto3.client("s3")
        
        s3.put_object(
            Body=file_path,
            Bucket=bucket_name,
            Key=f"{key_name}.json"
        )
        
        logging.info(f"Data successfully uploaded to S3 bucket: {bucket_name}")
    except Exception as e:
        logging.error(f"Error uploading file to S3: {e}")