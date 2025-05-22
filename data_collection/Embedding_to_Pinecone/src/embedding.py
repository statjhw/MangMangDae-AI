from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import torch
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from .db import Pinecone
from .logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

class EmbeddingProcessor:
    """
    텍스트 임베딩을 생성하고 Pinecone에 업로드하는 클래스
    """
    
    def __init__(self, batch_size: int = 100):
        """
        임베딩 프로세서 초기화
        
        Args:
            batch_size: Pinecone 업로드 시 배치 크기
        """
        load_dotenv()
        self.batch_size = batch_size
        self.embedding_model = self._initialize_embedding_model()
        self.vectorstore = Pinecone(embedding_model=self.embedding_model).index
        
    def _initialize_embedding_model(self) -> HuggingFaceEmbeddings:
        """
        HuggingFace 임베딩 모델 초기화
        
        Returns:
            초기화된 임베딩 모델
        """
        try:
            return HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.error(f"모델 다운로드 중 오류 발생: {e}", exc_info=True)
            logger.info("다시 시도합니다...")
            return HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
    
    def create_document(self, content: str, doc_id: int) -> Document:
        """
        임베딩용 문서 생성
        
        Args:
            content: 문서 내용
            doc_id: 문서 ID
            
        Returns:
            생성된 Document 객체
        """
        return Document(
            page_content=f"[document] {content}",
            metadata={"id": doc_id}
        )
    
    def process_batch(self, documents: List[Dict[str, Any]], start_id: int = 1) -> None:
        """
        문서 배치를 처리하여 임베딩 생성 후 Pinecone에 업로드
        
        Args:
            documents: 처리할 문서 리스트
            start_id: 시작 ID (기본값: 1)
        """
        doc_objects = []
        doc_ids = []
        
        for i, doc in enumerate(documents, start=start_id):
            doc_object = self.create_document(doc['content'], i)
            doc_objects.append(doc_object)
            doc_ids.append(f"doc-{i}")
        
        # 배치 단위로 처리
        for i in range(0, len(doc_objects), self.batch_size):
            batch = doc_objects[i:i + self.batch_size]
            batch_ids = doc_ids[i:i + self.batch_size]
            
            try:
                self.vectorstore.add_documents(batch, ids=batch_ids)
                logger.info(f"배치 처리 완료: {i+1}~{min(i+self.batch_size, len(doc_objects))} / {len(doc_objects)}")
            except Exception as e:
                logger.error(f"배치 처리 중 오류 발생: {e}", exc_info=True)
                continue
