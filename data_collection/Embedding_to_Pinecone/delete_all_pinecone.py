from pinecone import Pinecone

pc = Pinecone(api_key="pcsk_4XFXCj_TPgMasWdVP3B2QpamesNghNhK1jXczJfy4nWAnSZfU3YRjkWY6h8JKkwQ9JcuyQ")
index = pc.Index("mmdindex")
index.delete(delete_all=True)
print("✅ Pinecone 인덱스 전체 삭제 완료!") 