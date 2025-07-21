from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from config import get_pinecone
import re
import torch

# 지연 로딩을 위한 함수
def get_embeddings():
    return HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            ) 

def get_vector_store():
    embeddings = get_embeddings()
    index = get_pinecone()
    return PineconeVectorStore(index=index, embedding=embeddings)

# def retrieve(query: str, top_k: int = 5):
#     embeddings = get_embeddings()
#     query_vector = embeddings.embed_query(query)

#     index = get_pinecone()
#     results = index.query(vector=query_vector, top_k=top_k, include_values=False, include_metadata=True)

#     distances = [x['score'] for x in results['matches']]
#     meta_data_li = [x['metadata'] for x in results['matches']]
#     text_data_li = [x['text'] for x in meta_data_li]
#     return distances, text_data_li

def retrieve(query: str, top_k: int = 5, exclude_urls: list = None):
    """
    쿼리와의 유사도를 기반으로 문서를 검색하며, 코드 레벨에서 특정 URL을 제외합니다.
    """
    if exclude_urls is None:
        exclude_urls = []

    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)
    index = get_pinecone()

    # [핵심] 필터링을 위해 필요한 것보다 더 많은 문서를 가져옴 (예: 3배수)
    fetch_k = top_k * 3

    # Pinecone에서는 DB 레벨 필터링을 사용하지 않음
    results = index.query(
        vector=query_vector,
        top_k=fetch_k,
        include_values=False,
        include_metadata=True
    )

    final_scores = []
    final_texts = []

    # [핵심] 코드 레벨에서 필터링 수행
    for match in results['matches']:
        # 최종 결과 목록이 top_k 만큼 채워지면 중단
        if len(final_texts) >= top_k:
            break

        # 메타데이터에서 원본 텍스트 추출 (데이터 저장 방식에 따라 'text' 키는 다를 수 있음)
        doc_text = match.get('metadata', {}).get('text', '')
        if not doc_text:
            continue

        # 문서 텍스트에서 URL 파싱
        url_match = re.search(r"채용공고 URL:\s*(.*)", doc_text)
        if url_match:
            doc_url = url_match.group(1).strip()
            # 제외 목록에 없는 경우에만 최종 결과에 추가
            if doc_url not in exclude_urls:
                final_scores.append(match['score'])
                final_texts.append(doc_text)
        else:
            # URL이 없는 문서는 일단 포함 (혹은 비즈니스 로직에 따라 제외)
            final_scores.append(match['score'])
            final_texts.append(doc_text)
    
    return final_scores, final_texts
