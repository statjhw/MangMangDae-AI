import datetime
import json
import os
import time

import requests
from bs4 import BeautifulSoup
from driver import get_chrome_driver
from dynamodb import save_job_to_dynamodb
from logger import get_logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = get_logger(__name__)

# 전역 카운터 변수들
NOT_ELEMENT_COUNT = 0
TIMEOUT_EXCEPTION_COUNT = 0
ELEMENT_CLICK_INTERCEPT_COUNT = 0
EXCEPTION_COUNT = 0

class Crawler:
    def __init__(
            self,
            data_path=os.path.join(os.getcwd(), "data_collection", "backup"),
            site_name: str = "wanted"
    ):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Referer": "https://www.wanted.co.kr/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        }
        self.driver = get_chrome_driver()
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        self.data_path = data_path
        self.filenames = {
                    "url_list": os.path.join(data_path, f"{site_name}.url_list.json"),
                }
        self.site_name = site_name
        self.endpoint = f"https://www.{site_name}.co.kr"

        # mapping_table.json에서 직업 카테고리 정보 로딩
            # mapping_table.json 파일에서 직업 카테고리 매핑 정보 로드
        with open("data_collection/crawler/mapping_table.json") as f:
            raw_mapping = json.load(f)
            
            # 직업 ID를 이름으로 매핑하는 딕셔너리 생성
            self.job_category_id2name = {}
            for parent_category, job_map in raw_mapping.items():
                for job_id, name in job_map.items():
                    self.job_category_id2name[int(job_id)] = name
                    
        logger.info(f"직업 카테고리 매핑 로드 완료: {len(self.job_category_id2name)}개 항목")
        


        # 섹션명을 필드명으로 매핑하는 딕셔너리
        self.map_section_to_field = {
            "포지션 상세": "position_detail",
            "주요업무": "main_tasks",
            "자격요건": "qualifications",
            "우대사항": "preferred_qualifications",
            "혜택 및 복지": "benefits",
            "채용 전형": "hiring_process",
            "기술 스택 • 툴": "tech_stack",
        }

    def requests_get(self, url: str) -> requests.Response:
        with requests.Session() as s:
            response = s.get(url, headers=self.headers)
        return response
    
    def run(self):
        """
        전체 크롤링 프로세스를 실행하는 함수
        """
        logger.info("=== 크롤링 프로세스 시작 ===")
        
        try:
            # 1. URL 리스트 수집
            logger.info("1단계: URL 리스트 수집 시작")
            job_dict = self.get_url_list()
            logger.info(f"URL 리스트 수집 완료: {len(job_dict)}개 카테고리")
            
            # 2. 채용공고 정보 크롤링 및 DB 저장
            logger.info("2단계: 채용공고 크롤링 및 DB 저장 시작")
            processed_count = self.crawling_job_info(job_dict)
            
            logger.info("=== 크롤링 프로세스 완료 ===")              
        except Exception as e:
            logger.error(f"크롤링 프로세스 중 오류 발생: {e}")
            raise
        finally:
            # 드라이버 종료
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                logger.info("Chrome driver 종료 완료")

    def scroll_down_page(self, driver) -> str:
        page_source = ""
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            if page_source == driver.page_source:
                break
            else:
                page_source = driver.page_source

        return page_source
    
    def get_url_list(self):
        filename = self.filenames["url_list"]
        driver = self.driver

        job_dict = {}
        if os.path.exists(filename):
            with open(filename) as f:
                job_dict = json.load(f)

        with open("data_collection/crawler/mapping_table.json") as f:
            mapping_table = json.load(f)

        for job_parent_category, job_category_id2name in mapping_table.items():
            for job_category in job_category_id2name:
                if job_category in job_dict:
                    continue

                driver.get(
                    f"{self.endpoint}/wdlist/{job_parent_category}/{job_category}"
                )
                logger.info("job_category로 이동")

                logger.info("scroll_down_page 함수 호출 시작")
                page_source = self.scroll_down_page(driver)

                try:
                    soup = BeautifulSoup(page_source, "html.parser")
                    ul_element = soup.find("ul", {"data-cy": "job-list"})
                    position_list = [
                        a_tag["href"]
                        for a_tag in ul_element.find_all("a")
                        if a_tag.get("href", "").startswith("/wd/")
                    ]
                except Exception:
                    position_list = []

                job_dict[job_category] = {
                    "position_list": position_list,
                }

                with open(
                    os.path.join(self.data_path, f"{self.site_name}.url_list.json"), "w"
                ) as f:
                    logger.info("wanted.url_list.json 파일에 저장")
                    json.dump(job_dict, f)

        return job_dict
    
    def crawling_job_info(self, job_dict=None):
        """
        채용공고 정보를 크롤링하고 바로 DB에 저장하는 함수
        get_recruit_content_info와 postprocess 함수를 합친 버전
        """
        processed_count = 0

        logger.info("crawling_job_info 함수 실행 - 파일 저장 없이 바로 DB 저장")
        
        if job_dict is None:
            if os.path.exists(self.filenames["url_list"]):
                with open(self.filenames["url_list"]) as f:
                    job_dict = json.load(f)
            else:
                job_dict = {}
        
        driver = self.driver

        for job_category, job_info in job_dict.items():
            logger.info(f"처리 중인 직업 카테고리: {job_category}")
            
            for position_url in job_info["position_list"]:
                try:
                    # 채용공고 페이지로 이동
                    driver.get(f"{self.endpoint}{position_url}")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"❌ {position_url} ▶️ 클릭 중 알 수 없는 오류: {e}")
                    continue
                
                try:
                    # 사진의 HTML 구조에 맞게 더 구체적인 선택자 사용
                    primary_selector = "//span[@class='Button_Button__label__J05SX' and text()='상세 정보 더 보기']/ancestor::button"
                    elements = driver.find_elements(By.XPATH, primary_selector)
                    logger.info(f"상세 정보 버튼 요소 개수: {len(elements)}")
                    
                    current_selector = primary_selector
                    
                    if not elements: 
                        logger.info(f"{position_url} -> 기본 선택자로 버튼 요소 없음")
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
                        time.sleep(1)

                except TimeoutException:
                    logger.warning(f"{position_url} -> 버튼이 5초 내에 clickable 상태가 되지 않음")
                except ElementClickInterceptedException:
                    logger.warning(f"🚫 {position_url} ▶️ 클릭 시 다른 요소에 가려짐")
                except Exception as e:
                    logger.error(f"❌ {position_url} ▶️ 클릭 중 알 수 없는 오류: {e}")
                    
                # 페이지 소스 가져와서 바로 파싱
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")

                # 파싱 시작
                # Job Title
                try:
                    job_title = soup.find("h1", class_="wds-58fmok").text.strip()
                    logger.info(f"job_title: {job_title}")
                except Exception as e:
                    logger.error(f"job_title 찾기 실패 : {e}")
                try:
                    # Company Name and ID
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

                # Job Description
                try:
                    job_description_article = soup.find(
                        "article", class_="JobDescription_JobDescription__s2Keo"
                    )
                    detailed_content = {}
                    if job_description_article:
                        # Position Detail
                        position_detail_h2 = job_description_article.find(
                            "h2", class_="wds-16rl0sf"
                        )
                        if (
                            position_detail_h2
                            and position_detail_h2.text.strip() == "포지션 상세"
                        ):
                            position_detail_div = position_detail_h2.find_next_sibling(
                                "div",
                                class_="JobDescription_JobDescription__paragraph__wrapper__WPrKC",
                            )
                            if position_detail_div:
                                position_detail_span = position_detail_div.find(
                                    "span", class_="wds-h4ga6o"
                                )
                                if position_detail_span:
                                    position_detail_text = position_detail_span.get_text(
                                        separator="\n"
                                    ).strip()
                                    detailed_content["position_detail"] = position_detail_text

                        # Subsections
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
                                        detailed_content[
                                            self.map_section_to_field.get(
                                                section_title,
                                                section_title.lower().replace(" ", "_"),
                                            )
                                        ] = items
                                    else:
                                        detailed_content[
                                            self.map_section_to_field.get(
                                                section_title,
                                                section_title.lower().replace(" ", "_"),
                                            )
                                        ] = content_text
                except Exception as e:
                    logger.error(f"detailed_content 찾기 실패 : {e}")

                # 마감일
                try:
                    deadline = soup.find("span", class_="wds-1u1yyy").get_text()
                except Exception as e:
                    logger.error(f"deadline 찾기 실패 : {e}")
                
                # 위치
                try:
                    location = soup.find("span", class_="wds-1td1qmv").get_text()
                except Exception as e:
                    logger.error(f"location 찾기 실패 : {e}")

                # 경력 정보 추출 (HTML 구조에 맞게 수정)
                try:
                    career_info = soup.find("span", class_="JobHeader_JobHeader__Tools__Company__Info__b9P4Y wds-1pe0q6z").get_text()
                    logger.info(f"career_info: {career_info}")
                except Exception as e:
                    logger.error(f"career_info 찾기 실패 : {e}")

                # 결과 구성
                result = {
                    "url": f"https://www.wanted.co.kr{position_url}",
                    "crawled_at": datetime.datetime.utcnow().isoformat(),
                    "job_category": job_category,
                    "job_name": self.job_category_id2name.get(
                        int(job_category), job_category
                    ),
                    "title": job_title,
                    "company_name": company_name,
                    "company_id": company_id,
                    "dead_line": deadline,
                    "location": location,
                    "career": career_info,  # 경력 정보 추가
                    **detailed_content,
                }

                # DB에 바로 저장
                save_job_to_dynamodb(result)
                processed_count += 1
                
                logger.info(f"✅ {position_url} 처리 완료 - DB 저장 성공 (총 {processed_count}개 처리)")

        # 최종 통계 출력
        logger.info("=== 크롤링 완료 통계 ===")
        logger.info(f"총 처리된 채용공고: {processed_count}개")
        return processed_count

if __name__ == "__main__":
    crawler = Crawler()
    crawler.run()