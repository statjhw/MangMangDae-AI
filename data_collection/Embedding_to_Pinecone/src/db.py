import os
from dotenv import load_dotenv
import boto3
from langchain_pinecone import PineconeVectorStore
import psycopg2

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
        )
        self.table_name = "wanted_jobs"
        self.table = self.dynamodb.Table(self.table_name)
    
    def get_item(self, key):
        response = self.table.get_item(Key=key)
        return response.get('Item')

    def scan_items_generator(self, table_name, page_size=25):
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
            yield item
        
        # 페이지네이션 처리 - 다음 페이지가 있으면 계속 스캔
        while 'LastEvaluatedKey' in response:
            kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.scan(**kwargs)
            
            for item in response['Items']:
                yield item

class Pinecone:
    def __init__(self, embedding_model=None):
        self.api_key = PINECONE_API_KEY
        self.index_name = "mmdindex"
        self.embedding = embedding_model
        self.index = self.get_index()

    def get_index(self):
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

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print("PostgreSQL DB 연결 성공")
        except Exception as e:
            print(f"PostgreSQL DB 연결 실패: {str(e)}")
            
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("PostgreSQL DB 연결 종료")