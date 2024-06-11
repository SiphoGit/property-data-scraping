
# Property Data Scraping

This project involves scraping property data from two South African property companies.

#### Hosting and Functions:

- The solution is hosted on AWS with three Amazon Lambda functions.

    1. Monthly Scraping Lambda: Runs once a month to scrape the entire website.
    2. Daily Scraping Lambda: Runs daily to scrape only newly added properties.
    3. Notifications Lambda: Triggered when scraping functions fail or objects are uploaded to the S3 bucket, and then sends an email notification via Amazon SNS.

#### Triggers and Storage:

- Amazon EventBridge triggers the scraping functions at specified intervals.
- The scraped data is stored in an S3 bucket as JSON objects and can be explored using Amazon Athena.

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

## Architecture

![System Architecture]("images\architeture_diagram.png")

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
