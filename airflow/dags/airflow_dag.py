import airflow
import boto3

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

from scripts.rawson import rawson_page_url_scraper, rawson_scraper
from scripts.pam_golding import get_property_url, get_content
from scripts.inputs import provinces_urls
    

# Connects to the Amazon SNS
sns_client = boto3.client('sns', region_name='eu-west-1')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

# Dag details
dag = DAG(
    dag_id = 'property_data_scraping',
    default_args= default_args,
    description = 'property data scraping',
    start_date = airflow.utils.dates.days_ago(0),
    schedule_interval = None
)

# Get functions from scripts directory
def run_function(function_name):
    if function_name == 'rawson_page_urls':
        rawson_page_url_scraper()
    elif function_name == 'raswon_push_to_s3':
        rawson_scraper()
    elif function_name == 'pam_golding_page_urls':
        get_property_url(provinces_urls)
    elif function_name == 'pam_golding_push_to_s3':
        get_content()
    else:
        raise ValueError(f"Function {function_name} not found")

# Send failure alerts via Amazon SNS
def failure_alert(context):
    sns_client.publish(
        TopicArn = '{sns topic arn}',
        Message = f"Airflow: {context['task_instance'].task_id} Failed.",
        Subject = 'Property data Scraping Failure Alert'
    )

# Send success alerts via Amazon SNS    
def success_alert(context):
    sns_client.publish(
        TopicArn = '{sns topic arn}',
        Message = f"Airflow: {context['task_instance'].task_id} Completed.",
        Subject = 'Data Scraping Completed!'
    )
    
# Dag tasks
start_task = BashOperator(
    task_id='start',
    bash_command='echo "Pipeline started"',
    dag=dag
)   

raswon_urls_task = PythonOperator(
    task_id='rawson_page_urls',
    python_callable= run_function,
    op_args=['rawson_page_urls'],
    dag=dag,
    on_failure_callback=failure_alert
)

pam_urls_task = PythonOperator(
    task_id='pam_golding_page_urls',
    python_callable=run_function,
    op_args=['pam_golding_page_urls'],
    dag=dag,
    on_failure_callback=failure_alert,
)

raswon_push_to_s3 = PythonOperator(
    task_id='raswon_push_to_s3',
    python_callable=run_function,
    op_args=['raswon_push_to_s3'],
    dag=dag,
    on_failure_callback=failure_alert
)

pam_golding_push_to_s3 = PythonOperator(
    task_id='pam_golding_push_to_s3',
    python_callable=run_function,
    op_args=['pam_golding_push_to_s3'],
    dag=dag,
    on_failure_callback=failure_alert,
)

end_task = BashOperator(
    task_id='end',
    bash_command='echo "Pipeline completed"',
    dag=dag,
    on_success_callback=success_alert
)  

# Data pipeline workflow
start_task >> [raswon_urls_task, pam_urls_task] 
raswon_urls_task >> raswon_push_to_s3 >> end_task
pam_urls_task >> pam_golding_push_to_s3 >> end_task