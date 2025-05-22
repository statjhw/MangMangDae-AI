import os
from dotenv import load_dotenv
from src.data_preprocessing import JobDataPreprocessor
from src.embedding import EmbeddingProcessor
from src.db import DynamoDB, Postgres

def main():
    """
    DynamoDB에서 채용 데이터를 가져와서 임베딩 후 Pinecone에 업로드하는 메인 함수
    """
    # 환경 변수 로드
    load_dotenv()
    
    # DynamoDB 리더 초기화
    dynamo_db = DynamoDB()
    
    # 전처리기 초기화
    preprocessor = JobDataPreprocessor()
    
    # 임베딩 프로세서 초기화 (배치 크기 100으로 설정)
    embedding_processor = EmbeddingProcessor(batch_size=100)
    
    try:
        print("DynamoDB에서 데이터 읽기 시작...")
        
        # PostgreSQL 연결
        postgres_db = Postgres()
        postgres_db.connect()
        
        # 현재까지 처리된 문서 수를 추적
        processed_count = 0
        raw_batch = []
        batch_size = 25  # DynamoDB 스캔 배치 크기
        
        # DynamoDB에서 데이터를 배치로 읽어오기
        for item in dynamo_db.scan_items_generator("wanted_jobs", page_size=batch_size):
            raw_batch.append(item)
            
            # 배치가 채워지면 처리
            if len(raw_batch) >= batch_size:
                # 데이터 전처리
                preprocessed_text = [preprocessor.preprocess(item) for item in raw_batch]
                
                # 임베딩 처리 (start_id는 현재까지 처리된 문서 수 + 1)
                documents = [{"content": text} for text in preprocessed_text]
                embedding_processor.process_batch(documents, start_id=processed_count + 1)
                
                # PostgreSQL에 Document ID와 URL 저장
                for i, item in enumerate(raw_batch, start=processed_count + 1):
                    job_id = i  # Document의 metadata ID
                    job_url = item.get('url')
                    if job_url:
                        postgres_db.insert_job_url(job_id, job_url)
                
                processed_count += len(raw_batch)
                print(f"총 {processed_count}개의 문서 전처리 및 임베딩 완료")
                
                # 배치 초기화
                raw_batch = []
        
        # 남은 배치 처리
        if raw_batch:
            # 데이터 전처리
            preprocessed_text = [preprocessor.preprocess(item) for item in raw_batch]
            
            # 임베딩 처리
            documents = [{"content": text} for text in preprocessed_text]
            embedding_processor.process_batch(documents, start_id=processed_count + 1)
            
            # PostgreSQL에 남은 Document ID와 URL 저장
            for i, item in enumerate(raw_batch, start=processed_count + 1):
                job_id = i # Document의 metadata ID
                job_url = item.get('url')
                if job_url:
                    postgres_db.insert_job_url(job_id, job_url)
            
            processed_count += len(raw_batch)
            print(f"총 {processed_count}개의 문서 전처리 및 임베딩 완료")
        
        # PostgreSQL 연결 종료
        postgres_db.disconnect()
        
        print("모든 데이터 처리가 완료되었습니다!")
            
    except Exception as e:
        print(f"처리 중 오류 발생: {e}")
        if 'postgres_db' in locals():
            postgres_db.disconnect()
        raise
    
if __name__ == "__main__":
    main() 