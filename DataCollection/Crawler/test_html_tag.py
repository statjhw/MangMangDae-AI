import time
import requests
from bs4 import BeautifulSoup
from driver import get_chrome_driver
from logger import get_logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = get_logger(__name__)

def requests_get(self, url: str) -> requests.Response:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Referer": "https://www.wanted.co.kr/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    }
    with requests.Session() as s:
        response = s.get(url, headers=headers)
    return response

def test_html_tag():
    url = "https://www.wanted.co.kr/wd/295766"
    try:
        driver = get_chrome_driver()
        driver.get(url)
    except Exception as e:
        logger.error(f"❌ {url} ▶️ 클릭 중 알 수 없는 오류: {e}")
        return False
    
    try:
        # 사진의 HTML 구조에 맞게 더 구체적인 선택자 사용
        primary_selector = "//span[@class='Button_Button__label__J05SX' and text()='상세 정보 더 보기']/ancestor::button"
        elements = driver.find_elements(By.XPATH, primary_selector)
        logger.info(f"상세 정보 버튼 요소 개수: {len(elements)}")
        
        current_selector = primary_selector
        
        if not elements: 
            logger.info(f"{url} -> 기본 선택자로 버튼 요소 없음")
            # 대안 선택자들 시도
            fallback_selectors = [
                "//button[contains(@class, 'Button_Button__root')]//span[text()='상세 정보 더 보기']/..",
                "//span[text()='상세 정보 더 보기']/ancestor::button",
                "//button[.//span[text()='상세 정보 더 보기']]"
            ]
            logger.info(f"fallback_selectors: {fallback_selectors}")
            for selector in fallback_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info(f"대안 선택자로 찾음: {selector}, 요소 개수: {len(elements)}")
                        current_selector = selector
                        break
                except Exception as e:
                    logger.warning(f"대안 선택자 실패 {selector}: {e}")
                    continue
        
        if elements:
            wait = WebDriverWait(driver, 5)
            more_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, current_selector))
            )
            more_button.click()
            time.sleep(3)

    except TimeoutException:
        logger.warning(f"{url} -> 버튼이 5초 내에 clickable 상태가 되지 않음")
    except ElementClickInterceptedException:
        logger.warning(f"🚫 {url} ▶️ 클릭 시 다른 요소에 가려짐")
    except Exception as e:
        logger.error(f"❌ {url} ▶️ 클릭 중 알 수 없는 오류: {e}")
        return False

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    
    #데이터 정보 실험하기
    
    ### 직업 이름 찾기
    try:
        job_title = soup.find("h1", class_="wds-58fmok").text.strip()
        logger.info(f"job_title: {job_title}")
    except Exception as e:
        logger.error(f"job_title 찾기 실패 : {e}")
        return False
    
    ### 회사 이름 찾기
    try:
        company_name_element = soup.find(
                        "strong", class_="CompanyInfo_CompanyInfo__name__sBeI6"
                    )
        company_name = (
            company_name_element.text.strip() if company_name_element else None
        )
        company_link = soup.find(
            "a", class_="JobHeader_JobHeader__Tools__Company__Link__NoBQI"
        )
        company_id = (
            company_link["href"].split("/")[-1] if company_link else None
        )
        logger.info(f"company_name: {company_name}")
        logger.info(f"company_id: {company_id}")

    except Exception as e:
        logger.error(f"company_name 찾기 실패 : {e}")
        return False
    
    ### 회사 상세 정보 찾기
    try:
        job_description_article = soup.find(
                            "article", class_="JobDescription_JobDescription__s2Keo"
                        )
        if job_description_article:
            position_detail_h2 = job_description_article.find(
                "h2", class_="wds-16rl0sf"
            )
            if position_detail_h2 and position_detail_h2.text.strip() == "포지션 상세":
                position_detail_div = position_detail_h2.find_next_sibling(
                    "div", class_="JobDescription_JobDescription__paragraph__wrapper__WPrKC"
                )
                if position_detail_div:
                    position_detail_span = position_detail_div.find(
                        "span", class_="wds-h4ga6o"
                    )
                    if position_detail_span:
                        position_detail_text = position_detail_span.get_text(separator="\n").strip()
                        logger.info(f"position_detail_text: {position_detail_text}")
                    else:
                        logger.info(f"position_detail_span 없음")
                else:
                    logger.info(f"position_detail_div 없음")
            else:
                logger.info(f"position_detail_h2 없음")

            section_divs = job_description_article.find_all(
                "div", class_="JobDescription_JobDescription__paragraph__87w8I"
            )
            for section_div in section_divs:
                h3 = section_div.find("h3", class_="wds-17nsd6i")
                if h3:
                    section_title = h3.text.strip()
                    content_span = section_div.find("span", class_="wds-h4ga6o")
                    if content_span:
                        content_text = content_span.get_text(
                            separator="\n"
                        ).strip()
                        content_lines = [
                            line.strip()
                            for line in content_text.split("\n")
                            if line.strip()
                        ]
                        if content_lines and content_lines[0].startswith("•"):
                            items = [
                                line.lstrip("• ").strip()
                                for line in content_lines
                            ]
                            logger.info(f"section_title: {section_title}")
                            logger.info(f"items: {items}")
                        else:
                            logger.info(f"section_title: {section_title}")
                            logger.info(f"content_text: {content_text}")
                else:
                    logger.info(f"h3 없음")

            logger.info(f"position_detail_text: {position_detail_text}")

    except Exception as e:
        logger.error(f"position_detail_text 찾기 실패 : {e}")
        return False
    
    ### 마감일 찾기
    try:
        deadline = soup.find("span", class_="wds-1u1yyy").get_text()
        logger.info(f"deadline: {deadline}")
    except Exception as e:
        logger.error(f"deadline 찾기 실패 : {e}")
        return False
    
    ### 위치 찾기
    try:
        location = soup.find("span", class_="wds-1td1qmv").get_text()
        logger.info(f"location: {location}")
    except Exception as e:
        logger.error(f"location 찾기 실패 : {e}")
        return False
    
    ### 경력 정보 찾기
    try:
        career_info = soup.find_all("span", class_="JobHeader_JobHeader__Tools__Company__Info__b9P4Y wds-1pe0q6z")[1].get_text()
        logger.info(f"career_info: {career_info}")
    except Exception as e:
        logger.error(f"career_info 찾기 실패 : {e}")
        return False

    driver.quit()

    result = {
        "url": url,
        "job_title": job_title,
        "company_name": company_name,
        "company_id": company_id,
        "position_detail_text": position_detail_text,
        "deadline": deadline,
        "location": location,
        "career": career_info,
    }
    logger.info(f"result: {result}")
    return True

if __name__ == "__main__":
    if test_html_tag():
        logger.info("테스트 완료")
    else:
        logger.error("테스트 실패")