import os
import sys
# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from dotenv import load_dotenv
from src.data_preprocessing import JobDataPreprocessor
from src.embedding import EmbeddingProcessor
from db import DynamoDB, Postgres
from src.logger import setup_logger # 로거 임포트

# main.py용 로거 설정
logger = setup_logger(__name__)

def main():
    """
    DynamoDB에서 채용 데이터를 가져와서 임베딩 후 Pinecone에 업로드하는 메인 함수
    """
    logger.info("메인 파이프라인 시작")
    # 환경 변수 로드
    load_dotenv()
    
    # 초기화
    dynamo_db = DynamoDB()
    preprocessor = JobDataPreprocessor()
    embedding_processor = EmbeddingProcessor(batch_size=100)
    postgres_db = Postgres()
    
    try:
        logger.info("PostgreSQL 데이터베이스 연결 시도...")
        if not postgres_db.connect(): # 연결 성공 여부 확인
            logger.critical("PostgreSQL 연결 실패. 파이프라인을 중단합니다.")
            return # 연결 실패 시 종료
        logger.info("PostgreSQL 연결 성공.")
        
        logger.info("DynamoDB에서 데이터 읽기 시작...")
        processed_count = 0
        raw_batch = []
        batch_size = 25  # DynamoDB 스캔 배치 크기
        
        for item in dynamo_db.scan_items_generator("wanted_jobs", page_size=batch_size):
            raw_batch.append(item)
            
            if len(raw_batch) >= batch_size:
                preprocessed_text = [preprocessor.preprocess(data) for data in raw_batch] # item -> data로 변경
                documents = [{"content": text} for text in preprocessed_text]
                embedding_processor.process_batch(documents, start_id=processed_count + 1)
                
                for i, batch_item in enumerate(raw_batch, start=processed_count + 1): # item -> batch_item으로 변경
                    job_id = i
                    job_url = batch_item.get('url')
                    if job_url:
                        postgres_db.insert_job_url(str(job_id), job_url) # job_id를 str로 변환
                
                processed_count += len(raw_batch)
                logger.info(f"총 {processed_count}개의 문서 전처리 및 임베딩 완료")
                raw_batch = []
        
        if raw_batch:
            preprocessed_text = [preprocessor.preprocess(data) for data in raw_batch] # item -> data로 변경
            documents = [{"content": text} for text in preprocessed_text]
            embedding_processor.process_batch(documents, start_id=processed_count + 1)
            
            for i, batch_item in enumerate(raw_batch, start=processed_count + 1): # item -> batch_item으로 변경
                job_id = i
                job_url = batch_item.get('url')
                if job_url:
                    postgres_db.insert_job_url(str(job_id), job_url) # job_id를 str로 변환
            
            processed_count += len(raw_batch)
            logger.info(f"총 {processed_count}개의 문서 전처리 및 임베딩 완료 (남은 배치)")
        
        logger.info("모든 데이터 처리가 완료되었습니다!")
            
    except Exception as e:
        logger.error(f"메인 파이프라인 처리 중 오류 발생: {e}", exc_info=True)
        # raise # 필요에 따라 에러를 다시 발생
    finally:
        # postgres_db 객체가 생성되었고, conn 객체가 None이 아닐 때만 disconnect 호출
        if hasattr(postgres_db, 'conn') and postgres_db.conn is not None:
            logger.info("PostgreSQL 연결 종료 시도...")
            postgres_db.disconnect()
        logger.info("메인 파이프라인 종료.")
    
if __name__ == "__main__":
    main()