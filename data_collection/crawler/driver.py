import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Selenium 로깅 레벨 조정
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)  # webdriver-manager 로그도 줄임

def get_chrome_driver():
    try:
        # 옵션 설정
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('detach', True)  # 브라우저 창이 자동으로 닫히지 않도록 설정
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # ChromeDriverManager를 사용하여 Chrome 버전에 맞는 드라이버 자동 설치
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome 드라이버 생성 성공")
        return driver
    except Exception as e: 
        print(f"driver 생성 에러: {str(e)}")
        return None