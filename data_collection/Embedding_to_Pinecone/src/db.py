import os
from dotenv import load_dotenv
import boto3
from langchain_pinecone import PineconeVectorStore
import psycopg2
from .logger import setup_logger # 로거 임포트

# 로거 설정
logger = setup_logger(__name__)

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

class DynamoDB:
    def __init__(self):
        self.access_key = AWS_ACCESS_KEY_ID
        self.secret_key = AWS_SECRET_ACCESS_KEY
        self.region = AWS_REGION
        self.dynamodb = boto3.resource(
            'dynamodb',  
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.table_name = "wanted_jobs"
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"DynamoDB class initialized. Table: {self.table_name}")
    
    def get_item(self, key):
        logger.debug(f"Attempting to get item with key: {key} from DynamoDB table: {self.table_name}")
        response = self.table.get_item(Key=key)
        item = response.get('Item')
        if item:
            logger.info(f"Successfully retrieved item with key: {key}")
        else:
            logger.warning(f"Item not found for key: {key}")
        return item

    def scan_items_generator(self, table_name, page_size=25):
        logger.info(f"Starting scan for DynamoDB table: {table_name} with page size: {page_size}")
        """
        DynamoDB 테이블의 항목을 페이지 단위로 반환하는 제너레이터입니다.
        메모리 사용량을 최적화하기 위해 한 번에 모든 항목을 로드하지 않고
        페이지 단위로 가져와 하나씩 반환합니다.
        
        Args:
            table_name (str): 테이블 이름
            page_size (int): 한 번에 가져올 항목 수 (기본값: 25)
            
        Yields:
            dict: 테이블의 각 항목
        """
        kwargs = {'Limit': page_size}
        
        # 첫 페이지 스캔
        response = self.table.scan(**kwargs)
        
        # 각 항목 반환
        for item in response['Items']:
            logger.debug(f"Yielding item: {item.get('url', 'N/A')} from scan") # Assuming 'url' exists for logging
            yield item
        
        # 페이지네이션 처리 - 다음 페이지가 있으면 계속 스캔
        while 'LastEvaluatedKey' in response:
            logger.debug(f"Fetching next page for scan, LastEvaluatedKey: {response['LastEvaluatedKey']}")
            kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.scan(**kwargs)
            
            for item in response['Items']:
                logger.debug(f"Yielding item: {item.get('url', 'N/A')} from paginated scan") # Assuming 'url' exists
                yield item
        logger.info(f"Finished scan for DynamoDB table: {table_name}")

class Pinecone:
    def __init__(self, embedding_model=None):
        self.api_key = PINECONE_API_KEY
        self.index_name = "mmdindex"
        self.embedding = embedding_model
        logger.info(f"Pinecone class initialized. Index name: {self.index_name}")
        self.index = self.get_index()

    def get_index(self):
        logger.info(f"Accessing Pinecone index: {self.index_name}")
        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embedding
        )

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