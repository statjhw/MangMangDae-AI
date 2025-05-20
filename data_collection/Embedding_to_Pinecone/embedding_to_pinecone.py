from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import json
import torch
import os

# ---------------------------
# 🔎 1. 임베딩 모델 준비
# ---------------------------
try:
    embedding_model = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large",
        model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
except Exception as e:
    print(f"모델 다운로드 중 오류 발생: {e}")
    print("다시 시도합니다...")
    embedding_model = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large",
        model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

# ---------------------------
# 📚 2. 문서 로딩 및 ID 부여
# ---------------------------
documents = []
ids = []

with open("wanted.result.updated.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        content = data.get("content", "")
        metadata = {
            "title": str(data.get("title", "") or ""),
            "source": str(data.get("source", "") or ""),
            "id": f"doc-{i}"
        }
        documents.append(Document(page_content=content, metadata=metadata))
        ids.append(f"doc-{i}")

# ---------------------------
# 📤 3. Pinecone에 업로드 (중복 방지)
# ---------------------------
index_name = "mmdindex"
vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embedding_model,
    pinecone_api_key=os.environ["PINECONE_API_KEY"]
)

batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    batch_ids = ids[i:i+batch_size]
    vectorstore.add_documents(batch, ids=batch_ids)

print("문서 임베딩 및 업로드가 완료되었습니다!")