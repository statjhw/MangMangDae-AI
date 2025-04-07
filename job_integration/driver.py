from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_chrome_driver():
    try:
        driver = webdriver.Chrome()
        return driver
    except: 
        print("driver 생성 에러")