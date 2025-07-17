import re
import json
import random
from collections import defaultdict
from typing import Dict, List, Tuple
from retrieval.embeddings import retrieve
from langchain_core.prompts import PromptTemplate
from config import get_llm

# 문서 샘플링 함수
def get_job_role_from_text(text: str) -> str:
    """문서 텍스트에서 '직무' 정보를 파싱합니다."""
    match = re.search(r"직무:\s*(.*?)\n", text)
    if match:
        return match.group(1).strip()
    return "기타"

def sample_diverse_documents(k: int) -> list:
    """다양한 직무의 문서 K개를 샘플링하는 함수"""
    print(f"=== 1단계: 다양한 직무의 문서 {k}개 샘플링 시작 ===")

    anchor_queries = [
        "서버 개발자", "프론트엔드 개발자", "자바 개발자", "파이썬 개발자",
        "데이터 엔지니어", "머신러닝 엔지니어", "안드로이드 개발자", "iOS 개발자",
        "DevOps / 시스템 관리자", "프로덕트 매니저", "서비스 기획자", "데이터 분석가",
        "사업개발 / 기획자", "디지털 마케터", "콘텐츠 마케터", "UX 디자이너",
        "UI, GUI 디자이너", "기술영업", "기업영업", "전자 엔지니어",
        "생산 관리자", "품질 관리자", "QA, 테스트 엔지니어", "게임 기획자"
    ]

    candidate_pool = {}
    print(f"총 {len(anchor_queries)}개의 앵커 쿼리로 문서를 수집합니다.")
    for query in anchor_queries:
        try:
            _, texts = retrieve(query, top_k=10)
            for text in texts:
                url_match = re.search(r"채용공고 URL:\s*(.*)", text)
                if url_match:
                    url = url_match.group(1).strip()
                    if url not in candidate_pool:
                        candidate_pool[url] = text
        except Exception as e:
            print(f"'{query}' 검색 중 오류 발생: {e}")

    print(f"\n총 {len(candidate_pool)}개의 고유한 후보 문서를 수집했습니다.")

    documents_by_role = defaultdict(list)
    for text in candidate_pool.values():
        role = get_job_role_from_text(text)
        documents_by_role[role].append(text)

    print(f"{len(documents_by_role)}개의 직무 그룹으로 분류 완료.")

    final_samples = []
    available_roles = list(documents_by_role.keys())
    random.shuffle(available_roles)

    for role in available_roles:
        if len(final_samples) < k and documents_by_role[role]:
            sample = random.choice(documents_by_role[role])
            final_samples.append(sample)
            documents_by_role[role].remove(sample)

    remaining_pool = [doc for role_docs in documents_by_role.values() for doc in role_docs]

    if len(final_samples) < k:
        needed = k - len(final_samples)
        if len(remaining_pool) >= needed:
            final_samples.extend(random.sample(remaining_pool, needed))
        else:
            final_samples.extend(remaining_pool)

    print(f"총 {len(final_samples)}개의 문서 샘플링을 완료했습니다.\n")
    return final_samples


# 질문 생성 함수 
# LLM에게 역할을 부여하고 JSON 형식의 출력을 지시하는 프롬프트
QUESTION_GENERATION_PROMPT = PromptTemplate(
    input_variables=["document"],
    template="""당신은 주어진 채용 공고를 분석하여, 해당 공고에 지원할 만한 '가상의 지원자'가 취업 챗봇에게 할 법한 '첫 질문'을 생성하는 AI입니다.

[분석할 채용 공고]
{document}

[지시사항]
1.  **가상 지원자 프로필 추론**: 위 공고를 보고, 이 회사에 지원할 만한 가장 이상적인 지원자의 프로필(전공, 경력, 핵심 기술 스택)을 현실적으로 추론하세요.
2.  **정보 일반화 (매우 중요)**:
    * **직무명 일반화**: 공고에 나온 특정 직무명(예: '메인넷 백엔드 개발자')을 보고, 더 표준적이고 일반적인 직무명(예: '블록체인 엔지니어', '백엔드 개발자')으로 변환하세요.
    * **위치 일반화**: 공고의 상세 주소(예: '서울특별시 강남구 강남대로128길 4')를 보고, 사용자가 실제로 검색할 법한 '시' 또는 '구' 단위의 넓은 지역명(예: '서울 강남', '성남시 분당구')으로 변환하세요.
3.  **첫 질문 생성**: 추론한 프로필과 **일반화된 직무/위치**를 바탕으로, 이 지원자가 챗봇에게 '일자리를 찾아달라'고 요청하는 '첫 질문'을 두 가지 스타일로 생성하세요.
4.  **JSON 출력**: 생성된 프로필과 질문을 아래 [출력 JSON 형식]에 맞춰 출력하세요. 다른 설명은 절대 추가하지 마세요.

[출력 JSON 형식]
{{
  "sincere_question": {{
    "candidate_major": "추론한 전공",
    "candidate_interest": "**[일반화된 직무명]**",
    "candidate_career": "추론한 경력",
    "candidate_tech_stack": ["추론한 핵심 기술 스택 리스트"],
    "candidate_location": "**[일반화된 위치]**",
    "candidate_question": "추론한 프로필과 [일반화된 정보]를 바탕으로 생성한 자연스러운 첫 질문 문장"
  }},
  "insincere_question": {{
    "candidate_major": "",
    "candidate_interest": "**[일반화된 직무명]**",
    "candidate_career": "",
    "candidate_tech_stack": [],
    "candidate_location": "**[일반화된 위치]**",
    "candidate_question": "[일반화된 정보]의 핵심 키워드만 조합한 짧은 검색 질문"
  }}
}}
"""
)

def generate_questions_with_llm(document_text: str) -> Tuple[Dict, Dict]:
    if not document_text: return None, None
    try:
        llm = get_llm()
        chain = QUESTION_GENERATION_PROMPT | llm
        response = chain.invoke({"document": document_text})
        
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if not json_match:
            print(f"[오류] LLM이 유효한 JSON을 반환하지 않았습니다:\n{response.content}")
            return None, None
            
        result_json = json.loads(json_match.group(0))
        sincere_q = result_json.get("sincere_question")
        insincere_q = result_json.get("insincere_question")

        if not sincere_q or not insincere_q:
            print(f"[오류] LLM 결과에 필요한 키가 없습니다: {result_json}")
            return None, None

        return sincere_q, insincere_q
    except Exception as e:
        print(f"[오류] LLM 질문 생성 중 에러 발생: {e}")
        return None, None



if __name__ == '__main__':
    NUM_SAMPLES = 200
    sampled_documents = sample_diverse_documents(NUM_SAMPLES)
    evaluation_dataset = []
    
    print(f"=== 2단계: 샘플링된 문서 {len(sampled_documents)}개에 대해 LLM 질문 쌍 생성 시작 ===")
    for i, doc in enumerate(sampled_documents):
        print(f"  - {i+1}/{len(sampled_documents)}번째 문서 처리 중...")
        sincere_q, insincere_q = generate_questions_with_llm(doc)
        if sincere_q and insincere_q:
            evaluation_dataset.append({"query": sincere_q, "answer_doc": doc})
            evaluation_dataset.append({"query": insincere_q, "answer_doc": doc})
            
    print("\n=== 최종 데이터셋 생성 완료! ===")
    print(f"총 {len(evaluation_dataset)}개의 (질문-정답) 데이터 포인트가 생성되었습니다.")
    
    with open('retriever_evaluation_dataset_final_modified.json', 'w', encoding='utf-8') as f:
        json.dump(evaluation_dataset, f, ensure_ascii=False, indent=2)
    print("\n'retriever_evaluation_dataset_final.json' 파일로 저장되었습니다.")