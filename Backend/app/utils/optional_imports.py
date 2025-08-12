"""
선택적 import를 위한 유틸리티 모듈
프로덕션 환경에서는 무거운 ML 라이브러리를 제외하고 배포
"""
import os
from typing import Optional, Any

def safe_import(module_name: str, fallback: Optional[Any] = None):
    """안전한 모듈 import - 실패 시 fallback 반환"""
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError as e:
        if os.getenv('RAILWAY_ENVIRONMENT'):
            # 프로덕션 환경에서는 경고만 출력
            print(f"Warning: {module_name} not available in production: {e}")
            return fallback
        else:
            # 개발 환경에서는 에러 발생
            raise e

# ML 관련 모듈들의 선택적 import
def get_torch():
    """PyTorch 모듈 가져오기 (선택적)"""
    return safe_import('torch')

def get_transformers():
    """Transformers 모듈 가져오기 (선택적)"""
    return safe_import('transformers')

def get_sentence_transformers():
    """Sentence Transformers 모듈 가져오기 (선택적)"""
    return safe_import('sentence_transformers')

def get_langchain_huggingface():
    """LangChain HuggingFace 모듈 가져오기 (선택적)"""
    return safe_import('langchain_huggingface')

def is_ml_available() -> bool:
    """ML 라이브러리들이 사용 가능한지 확인"""
    torch = get_torch()
    return torch is not None
