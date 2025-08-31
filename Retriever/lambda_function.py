import json
import logging
import os
import re
from typing import Dict, List, Tuple, Union
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from sentence_transformers import SentenceTransformer, CrossEncoder

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 환경 변수
OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'opensearch_job')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-2')

# HuggingFace 캐시 디렉토리를 /tmp로 설정 (Lambda에서 쓰기 가능한 유일한 디렉토리)
os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
os.environ['HF_HOME'] = '/tmp/hf_cache'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp/sentence_transformers_cache'
os.environ['TORCH_HOME'] = '/tmp/torch_cache'

# 홈 디렉토리도 /tmp로 변경
os.environ['HOME'] = '/tmp'

# 전역 변수 (콜드 스타트 최적화)
_opensearch_client = None
_embedding_model = None
_reranker_model = None

def get_opensearch_client():
    """OpenSearch 클라이언트 초기화"""
    global _opensearch_client
    if _opensearch_client is None:
        logger.info("OpenSearch 클라이언트 초기화 중...")
        
        if not OPENSEARCH_HOST:
            raise ValueError("OPENSEARCH_HOST 환경변수가 설정되지 않았습니다.")
        
        # Lambda에서는 자동으로 IAM 역할 자격 증명 사용
        session = boto3.Session()
        credentials = session.get_credentials()
        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            AWS_REGION,
            'es',
            session_token=credentials.token
        )
        
        _opensearch_client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        logger.info("✅ OpenSearch 클라이언트 초기화 완료")
    
    return _opensearch_client

def get_embedding_model():
    """임베딩 모델 초기화"""
    global _embedding_model
    if _embedding_model is None:
        logger.info("임베딩 모델 초기화 중...")
        
        # 캐시 디렉토리 미리 생성
        import os
        cache_dir = '/tmp/sentence_transformers_cache'
        os.makedirs(cache_dir, exist_ok=True)
        
        _embedding_model = SentenceTransformer(
            'intfloat/multilingual-e5-large',
            cache_folder=cache_dir
        )
        logger.info("✅ 임베딩 모델 초기화 완료")
    
    return _embedding_model

def get_reranker_model():
    """리랭커 모델 초기화"""
    global _reranker_model
    if _reranker_model is None:
        logger.info("리랭커 모델 초기화 중...")
        
        # 캐시 디렉토리 미리 생성
        import os
        cache_dir = '/tmp/cross_encoder_cache'
        os.makedirs(cache_dir, exist_ok=True)
        
        _reranker_model = CrossEncoder(
            'cross-encoder/ms-marco-MiniLM-L-6-v2',
            max_length=256,
            device='cpu',
            cache_folder=cache_dir
        )
        logger.info("✅ 리랭커 모델 초기화 완료")
    
    return _reranker_model

def format_document_for_reranking(document: Dict) -> str:
    """문서를 리랭킹용 텍스트로 포맷팅"""
    if not document:
        return ""
    
    parts = []
    
    # 주요 필드들을 텍스트로 변환
    if document.get('title'):
        parts.append(f"직무: {document['title']}")
    if document.get('company_name'):
        parts.append(f"회사: {document['company_name']}")
    if document.get('position_detail'):
        parts.append(f"포지션 상세: {document['position_detail']}")
    if document.get('main_tasks') and isinstance(document['main_tasks'], list):
        parts.append(f"주요 업무: {', '.join(document['main_tasks'])}")
    if document.get('qualifications') and isinstance(document['qualifications'], list):
        parts.append(f"자격 요건: {', '.join(document['qualifications'])}")
    if document.get('location'):
        parts.append(f"위치: {document['location']}")
    
    return " | ".join(parts)

def _get_years_from_career(career: str) -> int:
    """'n년', 'n 년' 형식에서 숫자 n을 추출합니다."""
    # 숫자를 찾기 위한 정규식
    match = re.search(r'(\d+)', career)
    if match:
        return int(match.group(1))
    return 0  # 숫자가 없으면 0년(신입)으로 간주

def _build_career_filter(career: str) -> Union[dict, None]:
    """[업그레이드 버전] 사용자의 career 입력을 바탕으로 지능적인 OpenSearch filter 절을 생성합니다."""
    if not career:
        return None

    user_years = _get_years_from_career(career)

    # CASE 1: 사용자가 '신입'이거나 경력에 숫자가 없는 경우
    if user_years == 0 and ("신입" in career or "무관" in career):
        # '신입', '경력무관', '무관' 키워드가 포함된 문서를 모두 찾도록 유연하게 설정
        return {
            "bool": {
                "should": [
                    {"match": {"career": "신입"}},
                    {"match": {"career": "무관"}},
                    {"match": {"career": "경력무관"}}
                ],
                "minimum_should_match": 1
            }
        }

    # CASE 2: 사용자가 경력직인 경우 (숫자 년차 입력)
    if user_years > 0:
        return {
            "bool": {
                # 'must' 조건: 사용자가 입력한 경력 키워드를 포함해야 함
                "must": [
                    {"match": {"career": career}}
                ],
                # 'must_not' 조건: '신입'이라는 단어가 포함된 공고는 제외
                "must_not": [
                    {"match": {"career": "신입"}}
                ]
            }
        }
    
    # 위 조건에 해당하지 않으면 필터를 적용하지 않음
    return None

def build_search_query(user_profile: Dict, top_k: int = 5, exclude_ids: list = None) -> Dict:
    """업그레이드된 하이브리드 검색 쿼리 생성"""
    if exclude_ids is None:
        exclude_ids = []

    # 사용자 입력 파싱
    major = user_profile.get("candidate_major", "")
    interest = user_profile.get("candidate_interest", "")
    career = user_profile.get("candidate_career", "")
    tech_stack = " ".join(user_profile.get("candidate_tech_stack", []))
    location = user_profile.get("candidate_location", "")
    query_text = user_profile.get("candidate_question", "")
    
    # 임베딩 벡터 생성
    embedding_model = get_embedding_model()
    query_vector = embedding_model.encode(f"query: {query_text}").tolist()
    
    # 제외할 문서 ID 처리
    must_not_clauses = []
    if exclude_ids:
        must_not_clauses.append({"ids": {"values": exclude_ids}})
    
    # 경력 필터 생성
    filter_clauses = []
    career_filter = _build_career_filter(career)
    if career_filter:
        filter_clauses.append(career_filter)
    
    # 하이브리드 검색 쿼리
    search_query = {
        "query": {
            "bool": {
                "should": [
                    # 텍스트 매칭
                    {"multi_match": {"query": interest, "fields": ["job_name^3", "title^2", "position_detail"], "boost": 3.0}},
                    {"multi_match": {"query": tech_stack, "fields": ["position_detail", "preferred_qualifications", "qualifications"], "boost": 2.5}},
                    {"multi_match": {"query": f"{major}", "fields": ["qualifications", "preferred_qualifications"], "boost": 1.5}},
                    {"match": {"location": {"query": location, "boost": 1.2}}} if location else None,
                    # 벡터 검색
                    {"knn": {"content_embedding": {"vector": query_vector, "k": top_k * 2, "boost": 2.0}}}
                ],
                "filter": filter_clauses,
                "must_not": must_not_clauses,
                "minimum_should_match": 1
            }
        },
        "size": top_k,
        "_source": {"excludes": ["content_embedding"]}
    }
    
    # None 값 제거
    search_query["query"]["bool"]["should"] = [q for q in search_query["query"]["bool"]["should"] if q is not None]
    
    return search_query

def hybrid_search(user_profile: Dict, top_k: int = 5, exclude_ids: list = None, use_reranker: bool = True) -> Tuple[List[float], List[str], List[Dict]]:
    """하이브리드 검색 + 리랭킹 실행"""
    
    try:
        # 1단계: 더 많은 후보 검색 (리랭킹을 위해)
        retrieval_k = top_k * 5 if use_reranker else top_k
        if exclude_ids is None:
            exclude_ids = []
        search_query = build_search_query(user_profile, retrieval_k, exclude_ids)
        
        logger.info(f"🔍 1단계: OpenSearch에서 {retrieval_k}개 후보 검색 중...")
        
        # OpenSearch 검색 실행
        client = get_opensearch_client()
        response = client.search(
            index=OPENSEARCH_INDEX,
            body=search_query
        )
        
        # 초기 검색 결과
        initial_hits = response.get("hits", {}).get("hits", [])
        if not initial_hits:
            logger.info("검색 결과가 없습니다.")
            return [], [], []
        
        logger.info(f"✅ 1단계 완료: {len(initial_hits)}개 후보 검색됨")
        
        if not use_reranker:
            # 리랭킹 없이 바로 반환
            scores = [hit.get("_score", 0.0) for hit in initial_hits]
            doc_ids = [hit.get("_id", "") for hit in initial_hits]
            documents = [hit.get("_source", {}) for hit in initial_hits]
            return scores, doc_ids, documents
        
        # 2단계: 리랭킹
        logger.info("🔄 2단계: 리랭킹 진행 중...")
        
        reranker = get_reranker_model()
        
        # 리랭킹용 쿼리 생성
        query_for_rerank = f"{user_profile.get('candidate_interest', '')} {user_profile.get('candidate_question', '')}"
        
        # [쿼리, 문서] 쌍 생성
        sentence_pairs = []
        for hit in initial_hits:
            document_text = format_document_for_reranking(hit.get('_source', {}))
            sentence_pairs.append([query_for_rerank, document_text])
        
        # 리랭킹 점수 계산 (배치 크기 4로 메모리 절약)
        rerank_scores = reranker.predict(sentence_pairs, show_progress_bar=False, batch_size=4)
        
        # 점수와 문서를 묶어서 정렬
        scored_hits = list(zip(rerank_scores, initial_hits))
        scored_hits.sort(key=lambda x: x[0], reverse=True)
        
        # 최종 top_k개 선택
        final_results = scored_hits[:top_k]
        
        scores = [float(score) for score, hit in final_results]
        doc_ids = [hit.get("_id", "") for score, hit in final_results]
        documents = [hit.get("_source", {}) for score, hit in final_results]
        
        logger.info(f"✅ 2단계 완료: 최종 {len(scores)}개 결과 반환")
        return scores, doc_ids, documents
        
    except Exception as e:
        logger.error(f"❌ 하이브리드 검색 실패: {e}")
        return [], [], []

def lambda_handler(event, context):
    """Lambda 핸들러"""
    try:
        # 요청 데이터 파싱
        body = json.loads(event.get('body', '{}'))
        user_profile = body.get('user_profile', {})
        top_k = int(body.get('top_k', 5))
        exclude_ids = body.get('exclude_ids', [])
        
        if not user_profile:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'user_profile이 필요합니다'}, ensure_ascii=False)
            }
        
        # 하이브리드 검색 실행
        scores, doc_ids, documents = hybrid_search(
            user_profile=user_profile,
            top_k=top_k,
            exclude_ids=exclude_ids
        )
        
        # 응답 반환
        response_data = {
            'scores': scores,
            'doc_ids': doc_ids,
            'documents': documents
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"❌ Lambda 실행 오류: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': '서버 오류가 발생했습니다'}, ensure_ascii=False)
        }