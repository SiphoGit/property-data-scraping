
# Property Data Scraping

A data pipeline for scraping South African Property data.

#### Hosting and Functionality:

- The solution is hosted on AWS within a Linux EC2 instance

    1. The data pipeline runs on Apache Airflow, containerized within a Docker container on an Amazon EC2 instance.
    2. A Lambda function triggers the EC2 instance on a schedule (EventBridge) to start the data pipeline.
    3. The scraped data is stored in an S3 bucket. The bucket is mounted on the EC2 instance using S3FS-Fuse
    4. A notification is sent via Amazon SNS to indicate if the pipeline has failed or succeeded.

#### The data can be used to:
- Identify potential investment opportunities based on property value trends.
- Predict future property prices and market behavior.
- Generate market reports and insights.
- Monitor competitors' property listings and pricing strategies.

## Architecture

![Architecture Diagram](https://github.com/SiphoGit/property-data-scraping/blob/main/images/architeture_diagram2.png?raw=true)
![Architecture Diagram](https://github.com/SiphoGit/property-data-scraping/blob/main/images/architeture_diagram2.png?raw=true)

## Pre-requisites

- AWS account
- AWS Comand Line Interface(AWS CLI). Can be download here: [Download AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Python 3 [installed](https://www.python.org/downloads/)
- BeatifulSoup AWS Lambda layer. [Lambda ARNs](https://github.com/keithrozario/Klayers?tab=readme-ov-file#list-of-arns)
- Requests AWS Lambda layer. [Lambda ARNs](https://github.com/keithrozario/Klayers?tab=readme-ov-file#list-of-arns)
## Tech Stack

**Developement:** 
- VSCode
- Python
- BeautifulSoup
- boto3
- Amazon CLI
- GitHub

**Cloud:** 
- AWS
- Amazon:
    1. Lambda 
    2. EventBridge
    3. SNS
    4. S3 
    5. Athena

## Run Locally

Go to the project directory

```bash
cd my-project
```
Create a new development environment

```bash
python3 -m venv env
```

Clone the project

```bash
git clone https://github.com/SiphoGit/property-data-scraping
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run Script

```bash
python lambda_function.py
```

S3 bucket policy

```bash
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "FullAccessForSpecificUser",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::aws_account_id:user/username"
            },
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::BUCKET_NAME",
                "arn:aws:s3:::BUCKET_NAME/*"
            ]
        }
    ]
}
```

Connect to AWS

```bash
aws configure
```
