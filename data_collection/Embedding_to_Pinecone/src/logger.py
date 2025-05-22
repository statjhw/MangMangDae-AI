import logging

def setup_logger(logger_name, log_level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # 이미 핸들러가 설정되어 있다면 중복 추가 방지
    if logger.hasHandlers():
        logger.handlers.clear() # 기존 핸들러 제거 후 재설정

    # 포맷터 생성 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger