import os
import json
import logging
from typing import Tuple, List, Dict
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

try:
    import boto3
except ImportError:
    print("❌ boto3가 설치되지 않았습니다. pip install boto3를 실행하세요.")
    boto3 = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정값
LAMBDA_FUNCTION_NAME = os.environ.get('RETRIEVER_LAMBDA_FUNCTION', 'MangMangDae-Retriever')
print(LAMBDA_FUNCTION_NAME)
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-2')
print(AWS_REGION)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID_LAMBDA')
print(AWS_ACCESS_KEY_ID)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY_LAMBDA')
print(AWS_SECRET_ACCESS_KEY)

def hybrid_search(user_profile: dict, top_k: int = 5, exclude_ids: list = None) -> Tuple[List[float], List[str], List[Dict]]:
    """
    Lambda 함수를 호출하여 하이브리드 검색을 수행합니다.
    
    Args:
        user_profile (dict): 사용자 프로필 정보
        top_k (int): 반환할 결과 수
        exclude_ids (list): 제외할 문서 ID 리스트
    
    Returns:
        Tuple[List[float], List[str], List[Dict]]: (scores, doc_ids, documents)
    """
    
    if exclude_ids is None:
        exclude_ids = []
    
    # boto3 설치 확인
    if boto3 is None:
        logger.error("boto3가 설치되지 않았습니다.")
        return [], [], []
    
    # AWS 자격 증명 확인
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.error("AWS 자격 증명이 설정되지 않았습니다. .env 파일에 AWS_ACCESS_KEY_ID와 AWS_SECRET_ACCESS_KEY를 설정하세요.")
        return [], [], []
    
    try:
        # Lambda 클라이언트 생성
        lambda_client = boto3.client(
            'lambda',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # 요청 데이터 구성
        payload = {
            "body": json.dumps({
                "user_profile": user_profile,
                "top_k": top_k,
                "exclude_ids": exclude_ids
            }, ensure_ascii=False)
        }
        
        logger.info(f"🚀 Lambda 함수 '{LAMBDA_FUNCTION_NAME}' 호출 중...")
        
        # Lambda 함수 호출
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload, ensure_ascii=False)
        )
        
        # 응답 파싱
        response_payload = json.loads(response['Payload'].read())
        
        # 상태 코드 확인
        if response_payload.get('statusCode') != 200:
            error_body = response_payload.get('body', '알 수 없는 오류')
            try:
                error_detail = json.loads(error_body)
                logger.error(f"❌ Lambda 함수 실행 실패: {error_detail}")
            except:
                logger.error(f"❌ Lambda 함수 실행 실패: {error_body}")
            return [], [], []
        
        # 성공 응답 데이터 파싱
        result_data = json.loads(response_payload['body'])
        
        scores = result_data.get('scores', [])
        doc_ids = result_data.get('doc_ids', [])
        documents = result_data.get('documents', [])
        
        logger.info(f"✅ 검색 완료: {len(scores)}개 결과 반환")
        return scores, doc_ids, documents
        
    except Exception as e:
        logger.error(f"❌ Lambda 함수 호출 실패: {e}")
        return [], [], []

# 테스트 코드
if __name__ == "__main__":
    # 테스트 데이터
    test_user_profile = {
        "candidate_major": "컴퓨터공학",
        "candidate_interest": "백엔드 개발자", 
        "candidate_career": "3년",
        "candidate_tech_stack": ["Python", "Django", "PostgreSQL"],
        "candidate_location": "서울",
        "candidate_question": "백엔드 개발 포지션을 찾고 있습니다. Python과 Django를 사용하는 회사를 선호합니다."
    }
    
    print("\n=== 하이브리드 검색 테스트 ===")
    scores, doc_ids, documents = hybrid_search(test_user_profile, top_k=3)
    
    if scores:
        for i, (score, doc_id, document) in enumerate(zip(scores, doc_ids, documents), 1):
            print(f"\n[결과 {i}] 점수: {score:.4f}, ID: {doc_id}")
            print(f"  제목: {document.get('title', '정보 없음')}")
            print(f"  회사: {document.get('company_name', '정보 없음')}")
            print(f"  위치: {document.get('location', '정보 없음')}")
            print("-" * 50)
    else:
        print("❌ 검색 결과가 없습니다.")