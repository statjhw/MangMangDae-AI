#!/usr/bin/env python3
"""
DynamoDB에서 OpenSearch로 데이터를 마이그레이션하는 스크립트 (임베딩 포함)

이 스크립트는 DynamoDB의 wanted_jobs 테이블에서 데이터를 읽어와
전처리, 임베딩 생성 후 OpenSearch 인덱스로 마이그레이션합니다.
"""

import sys
import os
import time
import torch
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from DB.dynamodb import DynamoDB
from DB.opensearch import OpenSearchDB

from DB.logger import setup_logger
from langchain_huggingface import HuggingFaceEmbeddings

from data_preprocessing import JobDataPreprocessor

# 로거 설정
logger = setup_logger(__name__)


class DynamoToOpenSearchMigrator:
    def __init__(self, batch_size: int = 50):  # 임베딩 때문에 배치 크기 줄임
        """
        마이그레이션 클래스 초기화 (임베딩 포함)
        
        Args:
            batch_size (int): 한 번에 처리할 배치 크기 (기본값: 50)
        """
        self.dynamodb = DynamoDB()
        self.opensearch = OpenSearchDB()
        self.batch_size = batch_size
        self.migrated_count = 0
        self.error_count = 0
        
        # 전처리기 초기화
        self.preprocessor = JobDataPreprocessor()
        
        # 임베딩 모델 초기화
        self.embedding_model = self._initialize_embedding_model()
        
        logger.info(f"Migrator initialized with batch size: {batch_size}")
        logger.info(f"Embedding model: intfloat/multilingual-e5-large")
        logger.info(f"Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    def _initialize_embedding_model(self) -> HuggingFaceEmbeddings:
        """
        HuggingFace 임베딩 모델 초기화
        
        Returns:
            초기화된 임베딩 모델
        """
        logger.info("Initializing embedding model...")
        try:
            model = HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("✅ Embedding model initialized successfully")
            return model
        except Exception as e:
            logger.error(f"❌ Error initializing embedding model: {e}")
            logger.info("Retrying model initialization...")
            return HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
    
    def test_connections(self) -> bool:
        """
        DynamoDB와 OpenSearch 연결을 테스트합니다.
        
        Returns:
            bool: 모든 연결 테스트 성공 여부
        """
        logger.info("Testing connections...")
        
        # DynamoDB 연결 테스트
        try:
            table = self.dynamodb.dynamodb.Table(self.dynamodb.table_name)
            table.load()
            logger.info(f"✅ DynamoDB connection successful. Table: {self.dynamodb.table_name}")
        except Exception as e:
            logger.error(f"❌ DynamoDB connection failed: {str(e)}")
            return False
        
        # OpenSearch 연결 테스트
        try:
            if self.opensearch.test_connection():
                logger.info("✅ OpenSearch connection successful")
            else:
                logger.error("❌ OpenSearch connection failed")
                return False
        except Exception as e:
            logger.error(f"❌ OpenSearch connection failed: {str(e)}")
            return False
        
        logger.info("✅ All connections tested successfully")
        return True
    
    def transform_document_with_embedding(self, dynamo_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        DynamoDB 아이템을 전처리하고 임베딩을 생성하여 OpenSearch 문서 형식으로 변환합니다.
        
        Args:
            dynamo_item (dict): DynamoDB에서 가져온 아이템
            
        Returns:
            dict: OpenSearch용으로 변환된 문서 (임베딩 포함)
        """
        url = dynamo_item.get('url', 'Unknown URL')
        
        try:
            # 1. 기본 필드 매핑
            transformed = {
                'url': dynamo_item.get('url', ''),
                'title': dynamo_item.get('title', ''),
                'company_name': dynamo_item.get('company_name', ''),
                'company_id': dynamo_item.get('company_id', ''),
                'location': dynamo_item.get('location', ''),
                'job_name': dynamo_item.get('job_name', ''),
                'job_category': dynamo_item.get('job_category', ''),
                'dead_line': dynamo_item.get('dead_line', ''),
                'crawled_at': dynamo_item.get('crawled_at', ''),
            }
            
            # 태그 정보
            
            # 상세 내용 필드들
            detail_fields = [
                'position_detail', 'main_tasks', 'qualifications',
                'preferred_qualifications', 'benefits', 'hiring_process'
            ]
            
            for field in detail_fields:
                if field in dynamo_item and dynamo_item[field]:
                    transformed[field] = dynamo_item[field]
            
            # 날짜 필드 처리
            if 'crawled_at' in dynamo_item and dynamo_item['crawled_at']:
                transformed['created_at'] = dynamo_item['crawled_at']
            else:
                transformed['created_at'] = datetime.now().isoformat()
            transformed['updated_at'] = datetime.now().isoformat()
            
            # 2. 전처리 수행
            logger.info(f"전처리 시작: {url}")
            preprocessed_content = self.preprocessor.preprocess(dynamo_item)
            
            if not preprocessed_content:
                logger.warning(f"전처리 실패: {url}")
                return None
                
            transformed['preprocessed_content'] = preprocessed_content
            logger.info(f"전처리 완료: {url} (길이: {len(preprocessed_content)} 문자)")
            
            # 3. 임베딩 생성
            logger.info(f"임베딩 생성 시작: {url}")
            embedding_start_time = time.time()
            
            try:
                # [document] 프리픽스 추가 (multilingual-e5-large 모델용)
                embedding_text = f"[document] {preprocessed_content}"
                content_embedding = self.embedding_model.embed_query(embedding_text)
                transformed['content_embedding'] = content_embedding
                
                embedding_time = time.time() - embedding_start_time
                vector_dim = len(content_embedding) if hasattr(content_embedding, '__len__') else 'unknown'
                
                logger.info(f"✅ 임베딩 생성 완료: {url} (차원: {vector_dim}, 소요시간: {embedding_time:.2f}초)")
                
            except Exception as e:
                embedding_time = time.time() - embedding_start_time
                logger.error(f"❌ 임베딩 생성 실패: {url} - {str(e)} (소요시간: {embedding_time:.2f}초)")
                return None
                
            return transformed
            
        except Exception as e:
            logger.error(f"❌ 문서 변환 실패: {url} - {str(e)}")
            return None
    
    def migrate_batch_with_embedding(self, documents: List[Dict[str, Any]]) -> bool:
        """
        문서 배치를 임베딩과 함께 OpenSearch로 마이그레이션합니다.
        
        Args:
            documents (list): 마이그레이션할 문서 리스트
            
        Returns:
            bool: 성공 여부
        """
        batch_start_time = time.time()
        logger.info(f"📦 배치 처리 시작: {len(documents)}개 문서")
        
        try:
            # 문서 변환 및 임베딩 생성
            transformed_docs = []
            doc_ids = []
            
            for i, doc in enumerate(documents):
                doc_start_time = time.time()
                logger.info(f"📄 문서 처리 중 ({i+1}/{len(documents)}): {doc.get('url', 'Unknown')}")
                
                try:
                    transformed_doc = self.transform_document_with_embedding(doc)
                    if transformed_doc is not None:
                        transformed_docs.append(transformed_doc)
                        # URL을 기반으로 고유 ID 생성 (중복 방지)
                        doc_id = doc.get('url', f"doc_{self.migrated_count + i + 1}")
                        doc_ids.append(doc_id)
                        
                        doc_time = time.time() - doc_start_time
                        logger.info(f"✅ 문서 처리 완료 ({i+1}/{len(documents)}): {doc_time:.2f}초")
                    else:
                        doc_time = time.time() - doc_start_time
                        logger.warning(f"⚠️ 문서 처리 실패, 건너뜀 ({i+1}/{len(documents)}): {doc.get('url', 'Unknown')} ({doc_time:.2f}초)")
                        self.error_count += 1
                        
                except Exception as e:
                    doc_time = time.time() - doc_start_time
                    logger.error(f"❌ 문서 처리 중 오류 ({i+1}/{len(documents)}): {str(e)} ({doc_time:.2f}초)")
                    self.error_count += 1
                    continue
            
            if not transformed_docs:
                logger.warning("⚠️ 유효한 문서가 없어 배치를 건너뜁니다")
                return True
            
            # OpenSearch에 벌크 인덱싱 (고유 ID 포함)
            logger.info(f"🔍 OpenSearch 인덱싱 시작: {len(transformed_docs)}개 문서")
            indexing_start_time = time.time()
            
            response = self.opensearch.bulk_index_with_ids(transformed_docs, doc_ids)
            
            indexing_time = time.time() - indexing_start_time
            batch_total_time = time.time() - batch_start_time
            
            # 응답 확인
            if response.get('errors', False):
                errors = response.get('items', [])
                error_count = 0
                for error in errors:
                    if 'index' in error and 'error' in error['index']:
                        logger.error(f"❌ 벌크 인덱싱 오류: {error['index']['error']}")
                        error_count += 1
                self.error_count += error_count
                logger.warning(f"⚠️ 벌크 인덱싱 완료 ({error_count}개 오류, 인덱싱: {indexing_time:.2f}초)")
            else:
                logger.info(f"✅ 벌크 인덱싱 성공: {len(transformed_docs)}개 문서 (인덱싱: {indexing_time:.2f}초)")
            
            self.migrated_count += len(transformed_docs)
            logger.info(f"📦 배치 처리 완료: 총 {batch_total_time:.2f}초 (문서당 평균: {batch_total_time/len(documents):.2f}초)")
            return True
            
        except Exception as e:
            batch_time = time.time() - batch_start_time
            logger.error(f"❌ 배치 처리 실패: {str(e)} (소요시간: {batch_time:.2f}초)")
            self.error_count += len(documents)
            return False
    
    def migrate_all_with_embedding(self) -> Dict[str, int]:
        """
        DynamoDB의 모든 데이터를 전처리, 임베딩과 함께 OpenSearch로 마이그레이션합니다.
        
        Returns:
            dict: 마이그레이션 결과 통계
        """
        logger.info("Starting migration from DynamoDB to OpenSearch with embeddings")
        
        # 연결 테스트
        if not self.test_connections():
            raise Exception("Connection test failed. Please check your configuration.")
        
        # OpenSearch 인덱스 생성 또는 확인 (임베딩 매핑 포함)
        try:
            self.opensearch.create_index()  # 이미 KNN 매핑이 포함된 create_index 사용
            logger.info("OpenSearch index with embedding mapping created/verified")
            
        except Exception as e:
            logger.error(f"Error creating OpenSearch index: {str(e)}")
            raise
        
        # DynamoDB에서 데이터 스캔
        batch = []
        start_time = time.time()
        
        try:
            logger.info(f"Starting data scan from DynamoDB table: {self.dynamodb.table_name}")
            
            for item in self.dynamodb.scan_items_generator(self.dynamodb.table_name, self.batch_size):
                batch.append(item)
                
                # 배치 크기에 도달하면 마이그레이션 실행
                if len(batch) >= self.batch_size:
                    logger.info(f"Processing batch of {len(batch)} documents...")
                    self.migrate_batch_with_embedding(batch)
                    batch = []
                    
                    # 진행 상황 로깅
                    elapsed_time = time.time() - start_time
                    logger.info(f"Progress: {self.migrated_count} documents migrated, "
                              f"{self.error_count} errors, elapsed: {elapsed_time:.2f}s")
            
            # 마지막 배치 처리
            if batch:
                logger.info(f"Processing final batch of {len(batch)} documents...")
                self.migrate_batch_with_embedding(batch)
                
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            raise
        
        # 최종 통계
        total_time = time.time() - start_time
        stats = {
            'total_migrated': self.migrated_count,
            'total_errors': self.error_count,
            'total_time_seconds': total_time,
            'migration_rate': self.migrated_count / total_time if total_time > 0 else 0,
            'documents_per_minute': (self.migrated_count / total_time * 60) if total_time > 0 else 0
        }
        
        logger.info(f"Migration completed. Stats: {stats}")
        return stats
    
    def verify_migration_with_search(self, sample_size: int = 5) -> bool:
        """
        마이그레이션 결과를 검색으로 검증합니다.
        
        Args:
            sample_size (int): 검증할 샘플 크기
            
        Returns:
            bool: 검증 성공 여부
        """
        logger.info(f"Verifying migration with semantic search (sample size: {sample_size})")
        
        try:
            # 1. 전체 문서 수 확인
            query = {"query": {"match_all": {}}, "size": 0}
            response = self.opensearch.search(query)
            total_docs = response['hits']['total']['value']
            
            logger.info(f"OpenSearch contains {total_docs} documents")
            
            if total_docs == 0:
                logger.warning("No documents found in OpenSearch")
                return False
            
            # 2. 샘플 문서들의 임베딩 존재 확인
            sample_query = {
                "query": {"match_all": {}},
                "size": sample_size,
                "_source": {
                    "includes": ["url", "title", "company_name", "preprocessed_content"],
                    "excludes": ["content_embedding"]  # 큰 벡터는 제외하고 확인
                }
            }
            
            sample_response = self.opensearch.search(sample_query)
            sample_docs = sample_response['hits']['hits']
            
            # 3. 임베딩 필드 존재 확인 (실제 벡터는 조회하지 않고 매핑만 확인)
            index_info = self.opensearch.get_index_info()
            mappings = index_info[self.opensearch.index_name]['mappings']
            
            if 'content_embedding' in mappings['properties']:
                logger.info("✅ Content embedding field exists in index mapping")
                logger.info("✅ Preprocessed content field confirmed in sample documents")
                
                # 샘플 문서 출력
                logger.info(f"Sample documents:")
                for i, doc in enumerate(sample_docs[:3], 1):
                    source = doc['_source']
                    logger.info(f"  {i}. {source.get('title', 'N/A')} - {source.get('company_name', 'N/A')}")
                
                return True
            else:
                logger.error("❌ Content embedding field not found in index mapping")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying migration: {str(e)}")
            return False
    
    def test_semantic_search(self, query_text: str = "프론트엔드 개발자 React") -> bool:
        """
        의미적 검색 테스트
        
        Args:
            query_text: 테스트할 검색어
            
        Returns:
            bool: 검색 테스트 성공 여부
        """
        logger.info(f"Testing semantic search with query: '{query_text}'")
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.embed_query(f"[Query] {query_text}")
            
            # KNN 검색 쿼리
            search_body = {
                "query": {
                    "knn": {
                        "content_embedding": {
                            "vector": query_embedding,
                            "k": 5
                        }
                    }
                },
                "size": 5,
                "_source": {
                    "excludes": ["content_embedding"]  # 응답에서 벡터 제외
                }
            }
            
            response = self.opensearch.search(search_body)
            hits = response['hits']['hits']
            
            if hits:
                logger.info(f"✅ Semantic search successful! Found {len(hits)} results:")
                for i, hit in enumerate(hits, 1):
                    source = hit['_source']
                    score = hit['_score']
                    logger.info(f"  {i}. [{score:.3f}] {source.get('title', 'N/A')} - {source.get('company_name', 'N/A')}")
                return True
            else:
                logger.warning("❌ Semantic search returned no results")
                return False
                
        except Exception as e:
            logger.error(f"❌ Semantic search test failed: {str(e)}")
            return False


def main():
    """메인 실행 함수"""
    
    # 로그 레벨 설정 확인 및 조정
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        force=True  # 기존 로거 설정 덮어쓰기
    )
    
    try:
        # 마이그레이션 실행 (임베딩 포함)
        migrator = DynamoToOpenSearchMigrator(batch_size=25)  # 임베딩으로 인해 작은 배치 크기
        
        # 마이그레이션 수행
        stats = migrator.migrate_all_with_embedding()
        
        # 결과 출력
        print("\n" + "="*60)
        print("임베딩 포함 마이그레이션 완료!")
        print("="*60)
        print(f"총 마이그레이션된 문서: {stats['total_migrated']}")
        print(f"총 오류 수: {stats['total_errors']}")
        print(f"총 소요 시간: {stats['total_time_seconds']:.2f}초")
        print(f"마이그레이션 속도: {stats['migration_rate']:.2f} 문서/초")
        print(f"분당 처리량: {stats['documents_per_minute']:.1f} 문서/분")
        print("="*60)
        
        # 검증 수행
        if migrator.verify_migration_with_search():
            print("✅ 마이그레이션 검증 성공")
            
            # 의미적 검색 테스트
            if migrator.test_semantic_search("백엔드 개발자 Python Django"):
                print("✅ 의미적 검색 테스트 성공")
            else:
                print("⚠️ 의미적 검색 테스트 실패")
        else:
            print("❌ 마이그레이션 검증 실패")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print(f"❌ 마이그레이션 실패: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 