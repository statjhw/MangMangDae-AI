import os

import boto3
from dotenv import load_dotenv
from logger import get_logger

logger = get_logger()

try:
    load_dotenv()
    logger.info(".env 환경변수 불러오기 성공!")
except Exception as e:
    logger.info(".env 환경변수 불러오기 실패!\n" + f"message: {e}")

try:
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="ap-northeast-2",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    table = dynamodb.Table("wanted_jobs")
    logger.info("테이블 연결 성공!")
except Exception as e:
    logger.info("테이블 연결 실패!\n" + f"message: {e}")


def save_job_to_dynamodb(job_data: dict):
    """
    채용 정보를 DynamoDB에 저장
    :param job_data: 채용 정보 딕셔너리 (json 형태)
    """
    try:
        table.put_item(Item=job_data)
        logger.info("db 저장 성공!")
    except Exception as e:
        logger.info("db 저장 실패\n" + f"message: {e}")


def delete_all_items():
    try:
        scan = table.scan()
        items = scan.get("Items", [])

        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"url": item["url"]})

        logger.info(f"테이블의 모든 항목을 삭제 완료")
    except Exception as e:
        logger.info("테이블의 모든 항목 삭제 실패\n" + f"message: {e}")
