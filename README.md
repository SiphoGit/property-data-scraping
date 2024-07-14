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

## Pre-requisites

- [Create](https://www.python.org/downloads/) AWS account
- Lambda requests layer. [Lambda layers ARNs](https://www.python.org/downloads/)
- Python 3 [installed](https://www.python.org/downloads/)
- Docker. [Download Docker](https://docs.docker.com/desktop/install/windows-install/)
- Docker Hub Account. [Download Docker](https://hub.docker.com/)

## Tech Stack

**Development:** 
- VSCode
- Python
- BeautifulSoup
- boto3
- GitHub

**AWS:** 
1. EC2 
2. EventBridge
3. SNS
4. S3 
5. CloudWatch
    
**Data Pipeline Orchestration and Containerization:** 
- Apache Airflow
- Docker

## Architecture

![Architecture Diagram](https://github.com/SiphoGit/property-data-scraping/blob/main/images/architeture_diagram_2nd.png?raw=true)
![Architecture Diagram](https://github.com/SiphoGit/property-data-scraping/blob/main/images/dag_diagram.png?raw=true)

## Run Locally

Navigate to the project directory
```bash
cd ../my-project
```

Clone the project
```bash
https://github.com/SiphoGit/property-data-scraping .
```

Run Docker contaners (You need to be logged into Docker Desktop)
```bash
docker-compose build
```

Verify containers
```bash
docker-compose ps
```

Apache Airflow UI
```bash
http://localhost:8080/
```
## Run on AWS

**Security Groups**
```bash
Inbound rules:

| Type        | Protocol | Port Range |Description               |
|-------------|----------|------------|--------------------------|
| All traffic | All      | All        |Allow traffic from all IPs|

Outbound rules:

| Type        | Protocol | Port Range  | Destination               | Description                 |
|-------------|----------|-------------|---------------------------|-----------------------------|
| All traffic | All      | All         | 0.0.0.0/0                 | Allow all outbound          |
| All TCP     | TCP      | 0 - 65535   | Anywhere - IPv4. 0.0.0.0/0| Allow all TCP outbound IPv4 |
| All TCP     | TCP      | 0 - 65535   | Anywhere - IPv6. ::/0     | Allow all TCP outbound IPv6 |

```
**Connect to the EC2 instance using SSH**
```bash
ssh -i {key-pair}.pem -L 8080:localhost:8080 ubuntu@{instance-ip}
```

Create s3 bucket mount directory
```bash
sudo mkdir s3-mount
```

Mount S3 bucket on the EC2 instance
```bash
s3fs -o iam_role=<ec2-role> -o url="https://{aws-region}.amazonaws.com" -o endpoint={aws-region} -o curldbg {bucket-name} ~/s3-mount
```
