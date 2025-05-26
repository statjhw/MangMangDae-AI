import os
from dotenv import load_dotenv
import psycopg2
from .logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

load_dotenv()


class Postgres:
    def __init__(self):
        self.host = os.getenv("AWS_RDS_HOST")
        self.database = os.getenv("AWS_RDS_DB") 
        self.user = os.getenv("AWS_RDS_USER")
        self.password = os.getenv("AWS_RDS_PASSWORD")
        self.port = os.getenv("AWS_RDS_PORT", "5432")
        self.conn = None
        self.cursor = None
        logger.info("Postgres class initialized.")

    def connect(self):
        logger.info(f"Attempting to connect to PostgreSQL DB: {self.database} on host: {self.host}")
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            logger.info("PostgreSQL DB 연결 성공")
            self.create_job_urls_table()  # 테이블 생성 메서드 호출
            return True  # 연결 성공 시 True 반환
        except Exception as e:
            logger.error(f"PostgreSQL DB 연결 실패: {str(e)}", exc_info=True)
            return False # 연결 실패 시 False 반환

    def create_job_urls_table(self):
        logger.info("Attempting to create job_urls table if it does not exist.")
        """
        job_urls 테이블을 생성합니다.
        id (VARCHAR, PK), url (TEXT) 스키마를 가집니다.
        테이블이 이미 존재하면 생성하지 않습니다.
        """
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS job_urls (
                id VARCHAR(255) PRIMARY KEY,
                url TEXT NOT NULL
            );
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            logger.info("job_urls 테이블 생성 또는 이미 존재함.")
        except Exception as e:
            logger.error(f"job_urls 테이블 생성 실패: {str(e)}", exc_info=True)
            self.conn.rollback()  # 오류 발생 시 롤백
            
    def insert_job_url(self, job_id: str, url: str) -> bool:
        logger.info(f"Attempting to insert ID: {job_id}, URL: {url} into job_urls table.")
        """
        job_urls 테이블에 ID와 URL을 삽입합니다.
        ID가 이미 존재하면 삽입하지 않습니다.

        Args:
            job_id (str): 삽입할 레코드의 ID
            url (str): 삽입할 URL 값

        Returns:
            bool: 삽입 성공 시 True, 실패 또는 이미 존재 시 False
        """
        if not self.conn or not self.cursor:
            logger.warning("Cannot insert_job_url: Database not connected.")
            return False
        try:
            insert_query = """
            INSERT INTO job_urls (id, url)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;  -- ID가 충돌하면 아무 작업도 하지 않음
            """
            self.cursor.execute(insert_query, (job_id, url))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                logger.info(f"ID: {job_id}, URL: {url} 이(가) job_urls 테이블에 삽입되었습니다.")
                return True
            else:
                logger.info(f"ID: {job_id} 은(는) 이미 존재하여 삽입되지 않았습니다.")
                return False # 삽입된 행이 없는 경우 (이미 존재)
        except Exception as e:
            logger.error(f"데이터 삽입 실패 (ID: {job_id}): {str(e)}", exc_info=True)
            self.conn.rollback()
            return False

    def update_job_url(self, job_id: str, new_url: str) -> bool:
        logger.info(f"Attempting to update URL for ID: {job_id} to {new_url} in job_urls table.")
        """
        job_urls 테이블에서 주어진 ID에 해당하는 URL을 업데이트합니다.

        Args:
            job_id (str): 업데이트할 레코드의 ID
            new_url (str): 새로운 URL 값

        Returns:
            bool: 업데이트 성공 시 True, 실패 시 False
        """
        if not self.conn or not self.cursor:
            logger.warning("Cannot update_job_url: Database not connected.")
            return False
        try:
            update_query = """
            UPDATE job_urls
            SET url = %s
            WHERE id = %s;
            """
            self.cursor.execute(update_query, (new_url, job_id))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                logger.info(f"ID: {job_id}의 URL이(가) {new_url}(으)로 업데이트되었습니다.")
                return True
            else:
                logger.warning(f"ID: {job_id}에 해당하는 레코드가 없어 업데이트되지 않았습니다.")
                return False # 업데이트된 행이 없는 경우
        except Exception as e:
            logger.error(f"URL 업데이트 실패 (ID: {job_id}): {str(e)}", exc_info=True)
            self.conn.rollback()
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            logger.debug("PostgreSQL cursor closed.")
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL DB 연결 종료") 