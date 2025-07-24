import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_OPENSEARCH_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_OPENSEARCH_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "443"))
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "wanted_jobs")


class OpenSearchDB:
    def __init__(self):
        self.access_key = AWS_ACCESS_KEY_ID
        self.secret_key = AWS_SECRET_ACCESS_KEY
        self.region = AWS_REGION
        self.host = OPENSEARCH_HOST
        self.port = OPENSEARCH_PORT
        self.index_name = OPENSEARCH_INDEX
        
        # 환경 변수 검증
        self._validate_environment()
        
        # AWS 인증 설정
        credentials = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        ).get_credentials()
        
        self.awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            AWS_REGION,
            'es',
            session_token=credentials.token
        )
        
        # OpenSearch 클라이언트 초기화
        self.client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        logger.info(f"OpenSearch class initialized. Host: {self.host}, Index: {self.index_name}")
    
    def _validate_environment(self):
        """환경 변수 유효성을 검증합니다."""
        missing_vars = []
        
        if not AWS_ACCESS_KEY_ID:
            missing_vars.append("AWS_OPENSEARCH_ACCESS_KEY_ID")
        if not AWS_SECRET_ACCESS_KEY:
            missing_vars.append("AWS_OPENSEARCH_SECRET_ACCESS_KEY")
        if not AWS_REGION:
            missing_vars.append("AWS_REGION")
        if not OPENSEARCH_HOST:
            missing_vars.append("OPENSEARCH_HOST")
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def test_connection(self):
        """
        OpenSearch 연결을 테스트합니다.
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            # 클러스터 헬스 체크
            health = self.client.cluster.health()
            logger.info(f"OpenSearch cluster health: {health['status']}")
            
            # 인덱스 목록 조회
            indices = self.client.cat.indices(format='json')
            logger.info(f"Available indices: {[idx['index'] for idx in indices]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def create_index(self, index_name=None, mapping=None):
        """
        OpenSearch 인덱스를 생성합니다.
        
        Args:
            index_name (str): 인덱스 이름 (기본값: self.index_name)
            mapping (dict): 인덱스 매핑 설정
        """
        if index_name is None:
            index_name = self.index_name
            
        if mapping is None:
            mapping = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                "mappings": {
                    "properties": {
                        "url": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "company_name": {"type": "text", "analyzer": "standard"},
                        "company_id": {"type": "keyword"},
                        "location": {"type": "text", "analyzer": "standard"},
                        "job_name": {"type": "text", "analyzer": "standard"},
                        "job_category": {"type": "keyword"},
                        "dead_line": {"type": "text"},
                        "crawled_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                        "tag_name": {"type": "keyword"},
                        "tag_id": {"type": "keyword"},
                        "position_detail": {"type": "text", "analyzer": "standard"},
                        "main_tasks": {"type": "text", "analyzer": "standard"},
                        "qualifications": {"type": "text", "analyzer": "standard"},
                        "preferred_qualifications": {"type": "text", "analyzer": "standard"},
                        "benefits": {"type": "text", "analyzer": "standard"},
                        "hiring_process": {"type": "text", "analyzer": "standard"},
                        "tech_stack": {"type": "text", "analyzer": "standard"},
                        "created_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                        "updated_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},

                        #임베딩 관련 필드들 추가
                        "content_embedding": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                                "name": "hnsw",
                                "engine": "lucene",
                                "parameters": {
                                    "ef_construction": 108,
                                    "m": 16
                                }
                            }
                        },
                        "preprocessed_content": {
                            "type": "text",
                            "analyzer": "standard"
                    }
                }
            }
        }
            
        try:
            # 먼저 연결 테스트
            if not self.test_connection():
                raise Exception("OpenSearch connection test failed")
            
            if not self.client.indices.exists(index=index_name):
                response = self.client.indices.create(
                    index=index_name,
                    body=mapping
                )
                logger.info(f"Successfully created index: {index_name}")
                return response
            else:
                logger.info(f"Index {index_name} already exists")
                return None
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {str(e)}")
            # 더 자세한 오류 정보 제공
            if hasattr(e, 'info'):
                logger.error(f"Error details: {e.info}")
            raise


    def index_document(self, document, doc_id=None, index_name=None):
        """
        문서를 인덱스에 추가합니다.
        
        Args:
            document (dict): 인덱싱할 문서
            doc_id (str): 문서 ID (기본값: None, 자동 생성)
            index_name (str): 인덱스 이름 (기본값: self.index_name)
        """
        if index_name is None:
            index_name = self.index_name
            
        try:
            response = self.client.index(
                index=index_name,
                body=document,
                id=doc_id,
                refresh=True
            )
            logger.info(f"Successfully indexed document with ID: {response['_id']}")
            return response
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise
    
    def bulk_index_with_ids(self, documents, doc_ids, index_name=None):
        """
        여러 문서를 고유 ID와 함께 벌크로 인덱싱합니다.
        
        Args:
            documents (list): 인덱싱할 문서 리스트
            doc_ids (list): 문서 ID 리스트
            index_name (str): 인덱스 이름 (기본값: self.index_name)
        """
        if index_name is None:
            index_name = self.index_name
            
        if len(documents) != len(doc_ids):
            raise ValueError("Documents and doc_ids must have the same length")
            
        bulk_data = []
        for doc, doc_id in zip(documents, doc_ids):
            bulk_data.append({"index": {"_index": index_name, "_id": doc_id}})
            bulk_data.append(doc)
        
        try:
            response = self.client.bulk(body=bulk_data, refresh=True)
            logger.info(f"Successfully bulk indexed {len(documents)} documents with IDs")
            return response
        except Exception as e:
            logger.error(f"Error bulk indexing documents with IDs: {str(e)}")
            raise
    
    def bulk_index(self, documents, index_name=None):
        """
        여러 문서를 벌크로 인덱싱합니다.
        
        Args:
            documents (list): 인덱싱할 문서 리스트
            index_name (str): 인덱스 이름 (기본값: self.index_name)
        """
        if index_name is None:
            index_name = self.index_name
            
        bulk_data = []
        for doc in documents:
            bulk_data.append({"index": {"_index": index_name}})
            bulk_data.append(doc)
        
        try:
            response = self.client.bulk(body=bulk_data, refresh=True)
            logger.info(f"Successfully bulk indexed {len(documents)} documents")
            return response
        except Exception as e:
            logger.error(f"Error bulk indexing documents: {str(e)}")
            raise
    
    def search(self, query, index_name=None, size=10):
        """
        인덱스에서 검색을 수행합니다.
        
        Args:
            query (dict): 검색 쿼리
            index_name (str): 인덱스 이름 (기본값: self.index_name)
            size (int): 반환할 결과 수 (기본값: 10)
        """
        if index_name is None:
            index_name = self.index_name
            
        try:
            response = self.client.search(
                index=index_name,
                body=query,
                size=size
            )
            logger.info(f"Search completed. Found {response['hits']['total']['value']} documents")
            return response
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
    
    def delete_index(self, index_name=None):
        """
        인덱스를 삭제합니다.
        
        Args:
            index_name (str): 삭제할 인덱스 이름 (기본값: self.index_name)
        """
        if index_name is None:
            index_name = self.index_name
            
        try:
            response = self.client.indices.delete(index=index_name)
            logger.info(f"Successfully deleted index: {index_name}")
            return response
        except Exception as e:
            logger.error(f"Error deleting index {index_name}: {str(e)}")
            raise
    
    def get_index_info(self, index_name=None):
        """
        인덱스 정보를 조회합니다.
        
        Args:
            index_name (str): 조회할 인덱스 이름 (기본값: self.index_name)
        """
        if index_name is None:
            index_name = self.index_name
            
        try:
            response = self.client.indices.get(index=index_name)
            logger.info(f"Retrieved index info for: {index_name}")
            return response
        except Exception as e:
            logger.error(f"Error getting index info for {index_name}: {str(e)}")
            raise 

if __name__ == "__main__":
    opensearch = OpenSearchDB()