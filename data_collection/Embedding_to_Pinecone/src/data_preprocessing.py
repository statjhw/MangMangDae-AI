import re
from bs4 import BeautifulSoup
from .logger import setup_logger # 로거 임포트
from typing import Dict, List, Any, Optional

# 로거 설정
logger = setup_logger(__name__)

class JobDataPreprocessor:
    """
    채용 데이터를 임베딩에 최적화된 형태로 전처리하는 클래스
    """
    
    def __init__(self, max_tokens: int = 8000):
        """
        전처리기 초기화
        
        Args:
            max_tokens: 최대 토큰 수 제한
        """
        self.max_tokens = max_tokens
        self._current_id = 0  # ID 카운터 추가
        logger.info("DataPreprocessor class initialized.")
        
    def preprocess(self, job_data: Dict[str, Any]) -> str:
        """
        채용 데이터를 전처리하여 임베딩에 최적화된 텍스트로 변환
        
        Args:
            job_data: DynamoDB에서 가져온 채용 데이터
            
        Returns:
            임베딩에 최적화된 텍스트
        """
        logger.info(f"Starting data preprocessing for item URL: {job_data.get('url', 'N/A')}")
        try:
            text_parts = []
            
            # 직무 및 회사 정보 (가장 중요한 정보)
            job_title = f"직무: {job_data.get('title', '')}"
            text_parts.append(job_title)
            
            company = f"회사: {job_data.get('company_name', '')}"
            text_parts.append(company)
            
            job_category = f"직무 카테고리: {job_data.get('job_name', '')}"
            text_parts.append(job_category)
            
            # 태그 정보
            if job_data.get('tag_name'):
                tags = f"태그: {', '.join(job_data.get('tag_name', []))}"
                text_parts.append(tags)
            
            # 위치 및 마감일
            location = f"위치: {job_data.get('location', '')}"
            text_parts.append(location)
            
            deadline = f"마감일: {job_data.get('dead_line', '')}"
            text_parts.append(deadline)
            
            # 포지션 상세
            if job_data.get('position_detail'):
                position_detail = f"포지션 상세:\n{job_data.get('position_detail', '')}"
                text_parts.append(position_detail)
            
            # 주요 업무
            if job_data.get('main_tasks'):
                if isinstance(job_data['main_tasks'], list):
                    tasks = "\n- ".join(job_data['main_tasks'])
                    main_tasks = f"주요 업무:\n- {tasks}"
                else:
                    main_tasks = f"주요 업무:\n{job_data['main_tasks']}"
                text_parts.append(main_tasks)
            
            # 자격 요건
            if job_data.get('qualifications'):
                if isinstance(job_data['qualifications'], list):
                    quals = "\n- ".join(job_data['qualifications'])
                    qualifications = f"자격 요건:\n- {quals}"
                else:
                    qualifications = f"자격 요건:\n{job_data['qualifications']}"
                text_parts.append(qualifications)
            
            # 우대 사항
            if job_data.get('preferred_qualifications'):
                if isinstance(job_data['preferred_qualifications'], list):
                    prefs = "\n- ".join(job_data['preferred_qualifications'])
                    preferred = f"우대 사항:\n- {prefs}"
                else:
                    preferred = f"우대 사항:\n{job_data['preferred_qualifications']}"
                text_parts.append(preferred)
            
            # 기술 스택 (임베딩에서 중요한 부분)
            if job_data.get('tech_stack'):
                if isinstance(job_data['tech_stack'], list):
                    stack = ", ".join(job_data['tech_stack'])
                else:
                    stack = job_data['tech_stack']
                tech_stack = f"기술 스택: {stack}"
                text_parts.append(tech_stack)
                
                # 기술 스택 강조 (두 번 포함하여 가중치 부여)
                text_parts.append(f"사용 기술: {stack}")
            
            # 혜택 및 복지
            if job_data.get('benefits'):
                if isinstance(job_data['benefits'], list):
                    bens = "\n- ".join(job_data['benefits'])
                    benefits = f"혜택 및 복지:\n- {bens}"
                else:
                    benefits = f"혜택 및 복지:\n{job_data['benefits']}"
                text_parts.append(benefits)
            
            # 채용 과정
            if job_data.get('hiring_process'):
                hiring = f"채용 과정: {job_data.get('hiring_process', '')}"
                text_parts.append(hiring)
                
            # URL은 가장 마지막에 추가
            url = f"채용공고 URL: {job_data.get('url', '')}"
            text_parts.append(url)
            
            # 모든 섹션을 결합하고 불필요한 공백 제거
            combined_text = "\n\n".join(text_parts)
            
            # 텍스트 정규화
            normalized_text = self._normalize_text(combined_text)
            
            # HuggingFace E5 모델용 포맷팅: [document] 접두사 추가
            formatted_text = f"[document] {normalized_text}"
            
            logger.info(f"데이터 전처리 성공 - URL: {job_data.get('url', 'N/A')}")
            return formatted_text
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류 발생 - URL: {job_data.get('url', 'N/A')}: {str(e)}", exc_info=True)
            # 예외 처리 또는 재발생
            return None # 오류 상태 반환
    
    def _normalize_text(self, text: str) -> str:
        """
        텍스트 정규화
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정규화된 텍스트
        """
        # 여러 줄바꿈 정규화
        normalized = re.sub(r'\n{3,}', '\n\n', text)
        
        # 여러 공백 정규화
        normalized = re.sub(r'\s{2,}', ' ', normalized)
        
        return normalized.strip()