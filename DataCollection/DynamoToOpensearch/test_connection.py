#!/usr/bin/env python3
"""
OpenSearch 연결 테스트 스크립트

이 스크립트는 OpenSearch 연결과 권한을 테스트합니다.
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from DB.opensearch import OpenSearchDB
from DB.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)


def test_opensearch_connection():
    """OpenSearch 연결을 테스트합니다."""
    print("🔍 OpenSearch 연결 테스트 시작...")
    print("="*50)
    
    try:
        # OpenSearch 클라이언트 초기화
        print("1. OpenSearch 클라이언트 초기화...")
        opensearch = OpenSearchDB()
        print("✅ 클라이언트 초기화 성공")
        
        # 연결 테스트
        print("\n2. OpenSearch 연결 테스트...")
        if opensearch.test_connection():
            print("✅ 연결 테스트 성공")
        else:
            print("❌ 연결 테스트 실패")
            return False
        
        # 인덱스 존재 여부 확인
        print("\n3. 인덱스 존재 여부 확인...")
        index_name = opensearch.index_name
        try:
            exists = opensearch.client.indices.exists(index=index_name)
            if exists:
                print(f"✅ 인덱스 '{index_name}' 존재함")
                
                # 인덱스 정보 조회
                print("\n4. 인덱스 정보 조회...")
                try:
                    info = opensearch.get_index_info(index_name)
                    doc_count = info[index_name]['total']['docs']['count']
                    print(f"✅ 인덱스 문서 수: {doc_count}")
                except Exception as e:
                    print(f"⚠️ 인덱스 정보 조회 실패: {str(e)}")
            else:
                print(f"ℹ️ 인덱스 '{index_name}' 존재하지 않음")
        except Exception as e:
            print(f"❌ 인덱스 확인 실패: {str(e)}")
            return False
        
        # 권한 테스트 (인덱스 생성 시도)
        print("\n5. 인덱스 생성 권한 테스트...")
        test_index_name = f"{index_name}_test_permission"
        try:
            # 테스트 인덱스 생성
            mapping = {
                "mappings": {
                    "properties": {
                        "test": {"type": "keyword"}
                    }
                }
            }
            
            if not opensearch.client.indices.exists(index=test_index_name):
                response = opensearch.client.indices.create(
                    index=test_index_name,
                    body=mapping
                )
                print("✅ 인덱스 생성 권한 있음")
                
                # 테스트 문서 인덱싱
                print("\n6. 문서 인덱싱 권한 테스트...")
                try:
                    test_doc = {"test": "permission_test"}
                    response = opensearch.client.index(
                        index=test_index_name,
                        body=test_doc,
                        refresh=True
                    )
                    print("✅ 문서 인덱싱 권한 있음")
                    
                    # 테스트 문서 검색
                    print("\n7. 문서 검색 권한 테스트...")
                    try:
                        query = {"query": {"match_all": {}}}
                        response = opensearch.client.search(
                            index=test_index_name,
                            body=query
                        )
                        print("✅ 문서 검색 권한 있음")
                    except Exception as e:
                        print(f"❌ 문서 검색 권한 없음: {str(e)}")
                        return False
                    
                except Exception as e:
                    print(f"❌ 문서 인덱싱 권한 없음: {str(e)}")
                    return False
                
                # 테스트 인덱스 삭제
                try:
                    opensearch.client.indices.delete(index=test_index_name)
                    print("✅ 테스트 인덱스 삭제 완료")
                except Exception as e:
                    print(f"⚠️ 테스트 인덱스 삭제 실패: {str(e)}")
            else:
                print("ℹ️ 테스트 인덱스가 이미 존재함")
                
        except Exception as e:
            print(f"❌ 인덱스 생성 권한 없음: {str(e)}")
            return False
        
        print("\n" + "="*50)
        print("🎉 모든 테스트 통과!")
        print("✅ OpenSearch 연결 및 권한이 정상적으로 설정되어 있습니다.")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        print("\n🔧 문제 해결 방법:")
        print("1. 환경 변수 확인:")
        print("   - AWS_OPENSEARCH_ACCESS_KEY_ID")
        print("   - AWS_OPENSEARCH_SECRET_ACCESS_KEY")
        print("   - AWS_REGION")
        print("   - OPENSEARCH_HOST")
        print("   - OPENSEARCH_PORT")
        print("\n2. AWS IAM 권한 확인:")
        print("   - OpenSearch 도메인 접근 권한")
        print("   - 인덱스 생성/삭제 권한")
        print("   - 문서 인덱싱/검색 권한")
        print("\n3. 네트워크 연결 확인:")
        print("   - OpenSearch 엔드포인트 접근 가능 여부")
        print("   - 방화벽 설정")
        return False


def main():
    """메인 실행 함수"""
    success = test_opensearch_connection()
    
    if not success:
        print("\n❌ 연결 테스트 실패")
        sys.exit(1)
    else:
        print("\n✅ 연결 테스트 성공")


if __name__ == "__main__":
    main() 