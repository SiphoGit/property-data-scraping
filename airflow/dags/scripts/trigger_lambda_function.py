import json
import os
import time
import base64
import requests

def lambda_handler(event, context):
    # Airflow variables
    ec2_ip = os.environ['EC2_INSTANCE_IP']
    dag_id = event['dag_id']
    run_id = event.get('run_id', 'manual__' + str(int(time.time())))
    conf = event.get('conf', {})

    # Basic auth credentials
    airflow_username = os.environ['AIRFLOW_USERNAME']
    airflow_password = os.environ['AIRFLOW_PASSWORD']
    
    # Encode credentials
    auth = base64.b64encode(f"{airflow_username}:{airflow_password}".encode()).decode()

    # Airflow API URL
    url = f"{ec2_ip}:8080/api/v1/dags/{dag_id}/dagRuns"

    # Headers
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/json'
    }

    # Payload
    payload = {
        'dag_run_id': run_id,
        'conf': conf
    }

    # Make the request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Check the response
    if response.status_code == 200:
        return {
            'statusCode': 200,
            'body': json.dumps('DAG triggered successfully')
        }
    else:
        return {
            'statusCode': response.status_code,
            'body': json.dumps(response.text)
        }
