import logging
import os
from logging.handlers import RotatingFileHandler

# 로그 파일을 저장할 디렉토리 생성
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'app.log')

def setup_logger(logger_name, log_level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # 이미 핸들러가 설정되어 있다면 중복 추가 방지
    if logger.hasHandlers():
        logger.handlers.clear() # 기존 핸들러 제거 후 재설정 (혹은 return logger로 변경)

    # 포맷터 생성
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 설정 (RotatingFileHandler 사용, 최대 5MB, 3개 백업 파일 유지)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger 