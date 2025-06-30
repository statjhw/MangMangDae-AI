"""
DynamoDB to OpenSearch 마이그레이션 설정 파일

이 파일은 마이그레이션 과정에서 사용되는 설정들을 관리합니다.
"""

import os
from typing import Dict, Any

# 기본 마이그레이션 설정
DEFAULT_MIGRATION_CONFIG = {
    # 배치 처리 설정
    'batch_size': 100,
    'max_retries': 3,
    'retry_delay': 1,  # 초
    
    # 성능 설정
    'bulk_timeout': 30,  # 초
    'request_timeout': 60,  # 초
    
    # 로깅 설정
    'log_level': 'INFO',
    'progress_interval': 1000,  # 진행 상황 로깅 간격
    
    # 검증 설정
    'verification_sample_size': 10,
    
    # 필드 매핑 설정
    'field_mapping': {
        'url': 'url',
        'title': 'title', 
        'company': 'company',
        'location': 'location',
        'description': 'description',
        'requirements': 'requirements',
        'salary': 'salary',
        'job_type': 'job_type',
        'experience_level': 'experience_level',
        'skills': 'skills',
        'created_at': 'created_at',
        'updated_at': 'updated_at'
    },
    
    # OpenSearch 인덱스 설정
    'index_settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'refresh_interval': '1s'
    }
}

# OpenSearch 매핑 설정
OPENSEARCH_MAPPING = {
    "mappings": {
        "properties": {
            "url": {
                "type": "keyword",
                "index": True
            },
            "title": {
                "type": "text",
                "analyzer": "standard",
                "search_analyzer": "standard"
            },
            "company": {
                "type": "text",
                "analyzer": "standard"
            },
            "location": {
                "type": "text",
                "analyzer": "standard"
            },
            "description": {
                "type": "text",
                "analyzer": "standard"
            },
            "requirements": {
                "type": "text",
                "analyzer": "standard"
            },
            "salary": {
                "type": "text"
            },
            "job_type": {
                "type": "keyword"
            },
            "experience_level": {
                "type": "keyword"
            },
            "skills": {
                "type": "text",
                "analyzer": "standard"
            },
            "created_at": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            "updated_at": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "1s"
    }
}


def get_migration_config() -> Dict[str, Any]:
    """
    환경 변수와 기본 설정을 조합하여 마이그레이션 설정을 반환합니다.
    
    Returns:
        dict: 마이그레이션 설정
    """
    config = DEFAULT_MIGRATION_CONFIG.copy()
    
    # 환경 변수에서 설정 오버라이드
    if os.getenv('MIGRATION_BATCH_SIZE'):
        config['batch_size'] = int(os.getenv('MIGRATION_BATCH_SIZE'))
    
    if os.getenv('MIGRATION_MAX_RETRIES'):
        config['max_retries'] = int(os.getenv('MIGRATION_MAX_RETRIES'))
    
    if os.getenv('MIGRATION_RETRY_DELAY'):
        config['retry_delay'] = float(os.getenv('MIGRATION_RETRY_DELAY'))
    
    if os.getenv('MIGRATION_LOG_LEVEL'):
        config['log_level'] = os.getenv('MIGRATION_LOG_LEVEL')
    
    return config


def get_opensearch_mapping() -> Dict[str, Any]:
    """
    OpenSearch 매핑 설정을 반환합니다.
    
    Returns:
        dict: OpenSearch 매핑 설정
    """
    return OPENSEARCH_MAPPING.copy()


def validate_config(config: Dict[str, Any]) -> bool:
    """
    설정의 유효성을 검증합니다.
    
    Args:
        config (dict): 검증할 설정
        
    Returns:
        bool: 유효성 여부
    """
    required_fields = ['batch_size', 'max_retries', 'retry_delay']
    
    for field in required_fields:
        if field not in config:
            print(f"❌ 필수 설정 필드 누락: {field}")
            return False
    
    if config['batch_size'] <= 0:
        print("❌ batch_size는 0보다 커야 합니다")
        return False
    
    if config['max_retries'] < 0:
        print("❌ max_retries는 0 이상이어야 합니다")
        return False
    
    if config['retry_delay'] < 0:
        print("❌ retry_delay는 0 이상이어야 합니다")
        return False
    
    return True 