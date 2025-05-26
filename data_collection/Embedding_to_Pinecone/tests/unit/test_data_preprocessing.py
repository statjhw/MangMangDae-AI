import pytest
import sys
import os

# 현재 파일의 경로를 기준으로 src 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..', 'src')
sys.path.insert(0, src_dir)

# logger 모듈을 먼저 임포트하고 sys.modules에 등록하여 상대 임포트 문제 해결
import logger
sys.modules['data_preprocessing.logger'] = logger

from data_preprocessing import JobDataPreprocessor

@pytest.fixture
def preprocessor():
    """JobDataPreprocessor 인스턴스를 생성하는 fixture입니다."""
    return JobDataPreprocessor()

@pytest.fixture
def sample_job_data():
    """테스트에 사용할 샘플 채용 데이터를 반환하는 fixture입니다."""
    return {
        'id': 'test_id_123',
        'url': 'http://example.com/job/123',
        'title': '테스트 엔지니어',
        'company_name': '테스트 주식회사',
        'job_name': '소프트웨어 개발',
        'tag_name': ['Python', 'UnitTest'],
        'location': '서울',
        'dead_line': '2025-12-31',
        'position_detail': '상세 포지션 설명입니다.',
        'main_tasks': ['주요 업무 1', '주요 업무 2'],
        'qualifications': ['자격 요건 1', '자격 요건 2'],
        'preferred_qualifications': ['우대 사항 1', '우대 사항 2'],
        'tech_stack': ['Django', 'React'],
        'benefits': ['복지 혜택 1', '복지 혜택 2'],
        'hiring_process': '서류 -> 면접 -> 최종 합격'
    }

def test_preprocess_basic_functionality(preprocessor, sample_job_data):
    """preprocess 메서드의 기본적인 전처리 기능을 테스트합니다."""
    processed_text = preprocessor.preprocess(sample_job_data)
    
    assert processed_text is not None
    assert isinstance(processed_text, str)
    assert processed_text.startswith("직무: 테스트 엔지니어")
    assert "회사: 테스트 주식회사" in processed_text
    assert "태그: Python, UnitTest" in processed_text
    assert "주요 업무:\n- 주요 업무 1\n- 주요 업무 2" in processed_text
    assert "기술 스택: Django, React" in processed_text
    assert "사용 기술: Django, React" in processed_text  # 기술 스택 강조 확인
    assert "채용공고 URL: http://example.com/job/123" in processed_text

def test_preprocess_missing_fields(preprocessor):
    """일부 필드가 누락된 경우 preprocess 메서드의 동작을 테스트합니다."""
    partial_data = {
        'id': 'test_id_456',
        'url': 'http://example.com/job/456',
        'title': '부분 데이터 엔지니어',
        'company_name': '부분 주식회사'
        # 다른 필드들은 의도적으로 누락
    }
    
    processed_text = preprocessor.preprocess(partial_data)
    
    assert processed_text is not None
    assert processed_text.startswith("직무: 부분 데이터 엔지니어")
    assert "회사: 부분 주식회사" in processed_text
    assert "태그:" not in processed_text  # 누락된 필드는 포함되지 않아야 함

def test_preprocess_empty_input(preprocessor):
    """빈 딕셔너리가 입력될 경우 preprocess 메서드의 동작을 테스트합니다."""
    # 현재 구현은 빈 입력 또는 필수 값 누락 시 None을 반환하고 오류를 로깅합니다.
    processed_text = preprocessor.preprocess({})
    assert processed_text is None

def test_normalize_text(preprocessor):
    """_normalize_text 메서드의 텍스트 정규화 기능을 테스트합니다."""
    # 여러 줄바꿈 정규화 테스트
    text_with_extra_newlines = "첫 번째 줄.\n\n\n\n두 번째 줄."
    expected_newlines = "첫 번째 줄.\n\n두 번째 줄."
    assert preprocessor._normalize_text(text_with_extra_newlines) == expected_newlines

    # 여러 공백 정규화 테스트
    text_with_extra_spaces = "단어   사이   공백  많음."
    expected_spaces = "단어 사이 공백 많음."
    assert preprocessor._normalize_text(text_with_extra_spaces) == expected_spaces

    # 앞뒤 공백 제거 테스트
    text_with_leading_trailing_spaces = "  앞뒤 공백 있음  "
    expected_stripped = "앞뒤 공백 있음"
    assert preprocessor._normalize_text(text_with_leading_trailing_spaces) == expected_stripped
    
    # 복합 정규화 테스트
    text_complex = "  첫 문장.\n\n\n두번째 문장     이어짐.  \n\n세번째. "
    expected_complex = "첫 문장.\n\n두번째 문장 이어짐.\n\n세번째."
    assert preprocessor._normalize_text(text_complex) == expected_complex

def test_preprocess_string_type_for_list_fields(preprocessor, sample_job_data):
    """리스트가 와야 하는 필드에 문자열이 올 경우의 처리를 테스트합니다."""
    data = sample_job_data.copy()
    data['main_tasks'] = "단일 주요 업무"
    data['qualifications'] = "단일 자격 요건"
    data['tech_stack'] = "단일 기술"

    processed_text = preprocessor.preprocess(data)
    
    assert processed_text is not None
    assert "주요 업무:\n단일 주요 업무" in processed_text
    assert "자격 요건:\n단일 자격 요건" in processed_text
    assert "기술 스택: 단일 기술" in processed_text
    assert "사용 기술: 단일 기술" in processed_text

# pytest의 parametrize를 활용한 추가 테스트 예시
@pytest.mark.parametrize("field_name,field_value,expected_in_output", [
    ("title", "파라미터 테스트 엔지니어", "직무: 파라미터 테스트 엔지니어"),
    ("company_name", "파라미터 테스트 회사", "회사: 파라미터 테스트 회사"),
    ("location", "부산", "위치: 부산"),
])
def test_preprocess_individual_fields(preprocessor, field_name, field_value, expected_in_output):
    """개별 필드가 올바르게 처리되는지 parametrize를 사용하여 테스트합니다."""
    data = {field_name: field_value, 'url': 'http://test.com'}
    processed_text = preprocessor.preprocess(data)
    
    assert processed_text is not None
    assert expected_in_output in processed_text

if __name__ == '__main__':
    pytest.main([__file__]) 