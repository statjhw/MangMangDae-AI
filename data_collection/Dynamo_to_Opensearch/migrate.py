#!/usr/bin/env python3
"""
DynamoDB에서 OpenSearch로 데이터를 마이그레이션하는 스크립트

이 스크립트는 DynamoDB의 wanted_jobs 테이블에서 데이터를 읽어와
OpenSearch 인덱스로 마이그레이션합니다.
"""

import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db import DynamoDB, OpenSearchDB
from db.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)


class DynamoToOpenSearchMigrator:
    def __init__(self, batch_size: int = 100):
        """
        마이그레이션 클래스 초기화
        
        Args:
            batch_size (int): 한 번에 처리할 배치 크기 (기본값: 100)
        """
        self.dynamodb = DynamoDB()
        self.opensearch = OpenSearchDB()
        self.batch_size = batch_size
        self.migrated_count = 0
        self.error_count = 0
        
        logger.info(f"Migrator initialized with batch size: {batch_size}")
    
    def test_connections(self) -> bool:
        """
        DynamoDB와 OpenSearch 연결을 테스트합니다.
        
        Returns:
            bool: 모든 연결 테스트 성공 여부
        """
        logger.info("Testing connections...")
        
        # DynamoDB 연결 테스트
        try:
            # DynamoDB 테이블 존재 확인
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
    
    def transform_document(self, dynamo_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        DynamoDB 아이템을 OpenSearch 문서 형식으로 변환합니다.
        
        Args:
            dynamo_item (dict): DynamoDB에서 가져온 아이템
            
        Returns:
            dict: OpenSearch용으로 변환된 문서
        """
        # 기본 필드 매핑
        transformed = {
            'url': dynamo_item.get('url', ''),
            'title': dynamo_item.get('title', ''),
            'company': dynamo_item.get('company', ''),
            'location': dynamo_item.get('location', ''),
            'description': dynamo_item.get('description', ''),
            'requirements': dynamo_item.get('requirements', ''),
        }
        
        # 날짜 필드 처리
        if 'created_at' in dynamo_item:
            transformed['created_at'] = dynamo_item['created_at']
        else:
            transformed['created_at'] = datetime.now().isoformat()
            
        if 'updated_at' in dynamo_item:
            transformed['updated_at'] = dynamo_item['updated_at']
        else:
            transformed['updated_at'] = datetime.now().isoformat()
        
        # 추가 필드들 (있는 경우)
        additional_fields = ['salary', 'job_type', 'experience_level', 'skills']
        for field in additional_fields:
            if field in dynamo_item:
                transformed[field] = dynamo_item[field]
        
        return transformed
    
    def migrate_batch(self, documents: List[Dict[str, Any]]) -> bool:
        """
        문서 배치를 OpenSearch로 마이그레이션합니다.
        
        Args:
            documents (list): 마이그레이션할 문서 리스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 문서 변환
            transformed_docs = []
            for doc in documents:
                try:
                    transformed_doc = self.transform_document(doc)
                    transformed_docs.append(transformed_doc)
                except Exception as e:
                    logger.error(f"Error transforming document: {str(e)}")
                    self.error_count += 1
                    continue
            
            if not transformed_docs:
                logger.warning("No documents to migrate in this batch")
                return True
            
            # OpenSearch에 벌크 인덱싱
            response = self.opensearch.bulk_index(transformed_docs)
            
            # 응답 확인
            if response.get('errors', False):
                errors = response.get('items', [])
                for error in errors:
                    if 'index' in error and 'error' in error['index']:
                        logger.error(f"Bulk indexing error: {error['index']['error']}")
                        self.error_count += 1
                logger.warning(f"Bulk indexing completed with {len(errors)} errors")
            else:
                logger.info(f"Successfully migrated {len(transformed_docs)} documents")
            
            self.migrated_count += len(transformed_docs)
            return True
            
        except Exception as e:
            logger.error(f"Error migrating batch: {str(e)}")
            self.error_count += len(documents)
            return False
    
    def migrate_all(self) -> Dict[str, int]:
        """
        DynamoDB의 모든 데이터를 OpenSearch로 마이그레이션합니다.
        
        Returns:
            dict: 마이그레이션 결과 통계
        """
        logger.info("Starting migration from DynamoDB to OpenSearch")
        
        # 연결 테스트
        if not self.test_connections():
            raise Exception("Connection test failed. Please check your configuration.")
        
        # OpenSearch 인덱스 생성
        try:
            self.opensearch.create_index()
            logger.info("OpenSearch index created/verified")
        except Exception as e:
            logger.error(f"Error creating OpenSearch index: {str(e)}")
            raise
        
        # DynamoDB에서 데이터 스캔
        batch = []
        start_time = time.time()
        
        try:
            for item in self.dynamodb.scan_items_generator(self.dynamodb.table_name, self.batch_size):
                batch.append(item)
                
                # 배치 크기에 도달하면 마이그레이션 실행
                if len(batch) >= self.batch_size:
                    self.migrate_batch(batch)
                    batch = []
                    
                    # 진행 상황 로깅
                    elapsed_time = time.time() - start_time
                    logger.info(f"Progress: {self.migrated_count} documents migrated, "
                              f"{self.error_count} errors, elapsed: {elapsed_time:.2f}s")
            
            # 마지막 배치 처리
            if batch:
                self.migrate_batch(batch)
                
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            raise
        
        # 최종 통계
        total_time = time.time() - start_time
        stats = {
            'total_migrated': self.migrated_count,
            'total_errors': self.error_count,
            'total_time_seconds': total_time,
            'migration_rate': self.migrated_count / total_time if total_time > 0 else 0
        }
        
        logger.info(f"Migration completed. Stats: {stats}")
        return stats
    
    def verify_migration(self, sample_size: int = 10) -> bool:
        """
        마이그레이션 결과를 검증합니다.
        
        Args:
            sample_size (int): 검증할 샘플 크기
            
        Returns:
            bool: 검증 성공 여부
        """
        logger.info(f"Verifying migration with sample size: {sample_size}")
        
        try:
            # OpenSearch에서 샘플 검색
            query = {
                "query": {
                    "match_all": {}
                },
                "size": sample_size
            }
            
            response = self.opensearch.search(query)
            total_docs = response['hits']['total']['value']
            
            logger.info(f"OpenSearch contains {total_docs} documents")
            
            if total_docs > 0:
                logger.info("Migration verification successful")
                return True
            else:
                logger.warning("No documents found in OpenSearch")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying migration: {str(e)}")
            return False


def main():
    """메인 실행 함수"""
    try:
        # 마이그레이션 실행
        migrator = DynamoToOpenSearchMigrator(batch_size=100)
        
        # 마이그레이션 수행
        stats = migrator.migrate_all()
        
        # 결과 출력
        print("\n" + "="*50)
        print("마이그레이션 완료!")
        print("="*50)
        print(f"총 마이그레이션된 문서: {stats['total_migrated']}")
        print(f"총 오류 수: {stats['total_errors']}")
        print(f"총 소요 시간: {stats['total_time_seconds']:.2f}초")
        print(f"마이그레이션 속도: {stats['migration_rate']:.2f} 문서/초")
        print("="*50)
        
        # 검증 수행
        if migrator.verify_migration():
            print("✅ 마이그레이션 검증 성공")
        else:
            print("❌ 마이그레이션 검증 실패")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print(f"❌ 마이그레이션 실패: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 