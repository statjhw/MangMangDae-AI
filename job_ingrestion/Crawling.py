import os
import requests
import time
import json
import datetime
from logger import get_logger
from bs4 import BeautifulSoup
from dynamodb import save_job_to_dynamodb

from driver import get_chrome_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


logger = get_logger(__name__)

class Crawler:
    def __init__(self, data_path=os.path.join(os.getcwd(), "job_ingrestion", "backup"), site_name=""):
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Ggetko/20100101 Firefox/136.0'
        }
        self.driver = get_chrome_driver()
        if not os.path.exists(data_path) :
            os.mkdir(data_path)
        self.data_path = data_path
        self.site_name = site_name

        self.info_key2name = {
            "경력": "career",
            "학력": "academic_background",
            "마감일": "deadline",
            "근무지역": "location"
        }

        self.filenames = {
            "url_list": os.path.join(self.data_path, f"{self.site_name}.url_list.json"),
            "content_info": os.path.join(self.data_path, f"{self.site_name}.content_info.json"),
            "result": os.path.join(self.data_path, f"{self.site_name}.result.jsonl")
        }
    
    def requests_get(self, url: str) -> requests.Response:
        with requests.Session() as s :
            response = s.get(url, headers=self.headers)
        return response
    
    def run(self) :
        pass

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


class WanterCrawler(Crawler):
    def __init__(self, data_path=os.path.join(os.getcwd(), "job_ingrestion", "backup"), site_name="wanted"):
        super().__init__(data_path=data_path, site_name=site_name)
        self.endpoint = "https://www.wanted.co.kr"

        self.map_section_to_field = {
            "포지션 상세": "position_detail",
            "주요업무": "main_tasks",
            "자격요건": "qualifications",
            "우대사항": "preferred_qualifications",
            "혜택 및 복지": "benefits",
            "채용 전형": "hiring_process",
            "기술 스택 • 툴": "tech_stack",
        }

    def get_url_list(self) :
        filename = self.filenames["url_list"]
        driver = self.driver

        job_dict = {}
        if os.path.exists(filename):
            with open(filename) as f:
                job_dict = json.load(f)
        
        with open("job_ingrestion/mapping_table.json") as f :
            mapping_table = json.load(f)

        for job_parent_category,  job_category_id2name in mapping_table.items():
            for job_category in job_category_id2name :
                if job_category in job_dict: 
                    continue

                driver.get(f"{self.endpoint}/wdlist/{job_parent_category}/{job_category}")
                logger.info("job_category로 이동")

                logger.info("scroll_down_page 함수 호출 시작")
                page_source = self.scroll_down_page(driver)

                try : 
                    soup = BeautifulSoup(page_source, 'html.parser')
                    ul_element = soup.find('ul', {'data-cy': 'job-list'})
                    position_list = [
                        a_tag['href'] for a_tag in ul_element.find_all('a') if a_tag.get('href', '').startswith('/wd/')
                    ]
                except Exception :
                    position_list = []

                job_dict[job_category] = {
                    "page_source": page_source,
                    "position_list": position_list
                }

                with open(os.path.join(self.data_path, f"{self.site_name}.url_list.json"), "w") as f:
                    logger.info("wanted.url_list.json 파일에 저장")
                    json.dump(job_dict, f)

        return job_dict

    def get_recruit_content_info(self, job_dict=None):
        logger.info("get_recruit_content_info 함수 실행")
        if job_dict is None:
            if os.path.exists(self.filenames['url_list']):
                with open(self.filenames["url_list"]) as f:
                    job_dict = json.load(f)
            else:
                job_dict = {}

        filename = self.filenames["content_info"]
        driver = self.driver

        position_content_dict = {}
        if os.path.exists(filename):
            with open(filename) as f:
                position_content_dict = json.load(f)
        
    
        for job_category, job_info in job_dict.items():
            if job_category in position_content_dict:
                continue

            content_dict = {}
            for position_url in job_info["position_list"]:
                driver.get(f"{self.endpoint}{position_url}")
                time.sleep(1)
                
                try:    #추가 정보를 위해 더보기 창 클릭
                    wait = WebDriverWait(driver, 5)
                    more_button = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//span[text()='상세 정보 더 보기']/ancestor::button")
                    ))
                    more_button.click()
                    logger.info(f"{position_url}의 상세 정보 더 보기 버튼 클릭")
                    time.sleep(0.5)  # 클릭 후 데이터가 로드되도록 약간 대기
                except:
                    logger.info(f"{position_url}에는 '상세 정보 더 보기' 버튼이 없음")

                content_dict[position_url] = driver.page_source
                logger.info(f"{position_url}의 채용공고로 이동")
            position_content_dict[job_category] = content_dict

            with open(os.path.join(self.data_path, f"{self.site_name}.content_info.json"), "w") as f:
                json.dump(position_content_dict, f)
                logger.info(f"{job_category}의 content_info.json 저장")
        
        return position_content_dict

    def postprocess(self, position_content_dict=None):
        if position_content_dict is None:
            if os.path.exists(self.filenames["content_info"]):
                with open(self.filenames["content_info"]) as f:
                    position_content_dict = json.load(f)
            else:
                position_content_dict = self.get_recruit_content_info()

        file = open(self.filenames["result"], "w")

        postprocess_dict = {}
        if os.path.exists(self.filenames["content_info"]):
            with open(self.filenames["content_info"]) as f:
                postprocess_dict = json.load(f)
        
        # Process each job posting
        for job_category, info_dict in position_content_dict.items():
            for url, content in info_dict.items():
                soup = BeautifulSoup(content, 'html.parser')
                
                # Job Title
                job_title = soup.find("h1", class_="wds-jtr30u").text.strip() if soup.find("h1", class_="wds-jtr30u") else None
                
                # Company Name and ID
                company_name_element = soup.find("strong", class_="CompanyInfo_CompanyInfo__name__sBeI6")
                company_name = company_name_element.text.strip() if company_name_element else None
                
                company_link = soup.find("a", class_="JobHeader_JobHeader__Tools__Company__Link__NoBQI")
                company_id = company_link["href"].split("/")[-1] if company_link else None
                
                # Tags
                tags_article = soup.find("article", class_="CompanyTags_CompanyTags__OpNto")
                tag_name_list = []
                tag_id_list = []
                if tags_article:
                    tag_buttons = tags_article.find_all("button", class_="Button_Button__root__MS62F")
                    for tag_button in tag_buttons:
                        tag_name_span = tag_button.find("span", class_="wds-1m3gvmz")
                        if tag_name_span:
                            tag_name = tag_name_span.text.strip()
                            tag_id = tag_button.get("data-tag-id")
                            if tag_name and tag_id:
                                tag_name_list.append(tag_name)
                                tag_id_list.append(tag_id)
                
                # Job Description
                job_description_article = soup.find("article", class_="JobDescription_JobDescription__s2Keo")
                detailed_content = {}
                if job_description_article:
                    # Position Detail
                    position_detail_h2 = job_description_article.find("h2", class_="wds-qfl364")
                    if position_detail_h2 and position_detail_h2.text.strip() == "포지션 상세":
                        position_detail_div = position_detail_h2.find_next_sibling("div", class_="JobDescription_JobDescription__paragraph__wrapper__WPrKC")
                        if position_detail_div:
                            position_detail_span = position_detail_div.find("span", class_="wds-wcfcu3")
                            if position_detail_span:
                                position_detail_text = position_detail_span.get_text(separator='\n').strip()
                                detailed_content["position_detail"] = position_detail_text
                    
                    # Subsections
                    section_divs = job_description_article.find_all("div", class_="JobDescription_JobDescription__paragraph__87w8I")
                    logger.info(f"section_div의 갯수: {len(section_divs)}")
                    for section_div in section_divs:
                        h3 = section_div.find("h3", class_="wds-1y0suvb")
                        if h3:
                            section_title = h3.text.strip()
                            logger.info(section_title)
                            content_span = section_div.find("span", class_="wds-wcfcu3")
                            if content_span:
                                content_text = content_span.get_text(separator='\n').strip()
                                content_lines = [line.strip() for line in content_text.split('\n') if line.strip()]
                                if content_lines and content_lines[0].startswith('•'):
                                    items = [line.lstrip('• ').strip() for line in content_lines]
                                    detailed_content[self.map_section_to_field.get(section_title, section_title.lower().replace(" ", "_"))] = items
                                else:
                                    detailed_content[self.map_section_to_field.get(section_title, section_title.lower().replace(" ", "_"))] = content_text
                
                #마감일
                try:
                    deadline = soup.find("span", class_="wds-lgio6k").get_text()
                except:
                    deadline = "no_data"
                #위치 
                try: 
                    location = soup.find("span", class_="wds-1o4yxuk").get_text()
                except:
                    location = "no_data"
                

                # Construct result
                result = {
                    "url": f"https://www.wanted.co.kr{url}",
                    "crawled_at": datetime.datetime.utcnow().isoformat(),
                    "job_category": job_category,
                    "job_name": self.job_category_id2name.get(int(job_category), job_category),
                    "title": job_title,
                    "company_name": company_name,
                    "company_id": company_id,
                    "tag_name": tag_name_list,
                    "tag_id": tag_id_list,
                    "dead_line": deadline,
                    "location": location,
                    **detailed_content
                }
                save_job_to_dynamodb(result)
                # Write to file
                file.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        file.close()

    def run(self):
        job_dict = self.get_url_list()
        position_content_dict = self.get_recruit_content_info(job_dict)
        result_dict = self.postprocess(position_content_dict)
        return result_dict


