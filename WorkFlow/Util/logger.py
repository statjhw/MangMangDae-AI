import logging
import time
from functools import wraps
from datetime import datetime
from typing import Any, Optional

class NodeLogger:
    def __init__(self, node_name: str):
        self.logger = logging.getLogger(node_name)
        self.logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정 (간단한 형식)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        self.logger.addHandler(console_handler)
    
    def log_data(self, data: Any, description: str = "데이터"):
        """데이터 로깅"""
        self.logger.info(f"[{description}] {str(data)}")
    
    def log_process(self, message: str):
        """프로세스 로깅"""
        self.logger.info(f"[프로세스] {message}")
    
    def log_error(self, error: Exception, context: str = ""):
        """에러 로깅"""
        self.logger.error(f"[에러] {context}: {str(error)}")
    
    def log_metrics(self, metrics: dict):
        """메트릭 로깅"""
        self.logger.info(f"[메트릭] {metrics}")

def log_execution_time(logger: Optional[NodeLogger] = None):
    """함수 실행 시간을 측정하고 로깅하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if logger:
                    logger.log_metrics({
                        "함수": func.__name__,
                        "실행시간": f"{execution_time:.2f}초",
                        "상태": "성공"
                    })
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                
                if logger:
                    logger.log_metrics({
                        "함수": func.__name__,
                        "실행시간": f"{execution_time:.2f}초",
                        "상태": "실패",
                        "에러": str(e)
                    })
                raise
                
        return wrapper
    return decorator 