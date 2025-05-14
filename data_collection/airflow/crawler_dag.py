from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, "../backup")
CRAWLER_SCRIPT = os.path.join(BASE_DIR, "../crawler/main.py")

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='run_crawler_and_cleanup',
    default_args=default_args,
    description='크롤러 실행 + 백업 정리',
    schedule_interval='@daily',
    start_date=datetime(2024, 3, 28),
    catchup=False,
    tags=['crawler'],
) as dag:

    cleanup_task = BashOperator(
        task_id='cleanup_backup_folder',
        bash_command=f'rm -rf {BACKUP_DIR}/*'
    )

    run_crawler_task = BashOperator(
        task_id='run_crawler_script',
        bash_command=f'python {CRAWLER_SCRIPT}'
    )

    cleanup_task >> run_crawler_task
