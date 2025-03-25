import os
import requests
import time
import json
from bs4 import BeautifulSoup

from selenium import webdriver

class Crawler:
    def __init__(self, data_path=os.getcwd(), site_name=""):
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0'
        }
        self.driver = webdriver.safari
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
    def __init__(self, data_path=os.getcwd(), site_name="wanted"):
        super().__init__(data_path=data_path, site_name=site_name)
        self.endpoint = "https://www.wanted.co.kr"
        self.job_parent_category = 518 #개발자만
        self.job_category_id2name = {
            10110: "소프트웨어 엔지니어",
            873: "웹 개발자",
            872: "서버 개발자",
            669: "프론트엔드 개발자",
            660: "자바 개발자",
            900: "C,C++ 개발자",
            899: "파이썬 개발자",
            1634: "머신러닝 엔지니어",
            674: "DevOps / 시스템 관리자",
            665: "시스템,네트워크 관리자",
            655: "데이터 엔지니어",
            895: "Node.js 개발자",
            677: "안드로이드 개발자",
            678: "iOS 개발자",
            658: "임베디드 개발자",
            877: "개발 매니저",
            1024: "데이터 사이언티스트",
            1026: "기술지원",
            676: "QA,테스트 엔지니어",
            672: "하드웨어 엔지니어",
            1025: "빅데이터 엔지니어",
            671: "보안 엔지니어",
            876: "프로덕트 매니저",
            10111: "크로스플랫폼 앱 개발자",
            1027: "블록체인 플랫폼 엔지니어",
            10231: "DBA",
            893: "PHP 개발자",
            661: ".NET 개발자",
            896: "영상,음성 엔지니어",
            10230: "ERP전문가",
            939: "웹 퍼블리셔",
            898: "그래픽스 엔지니어",
            795: "CTO,Chief Technology Officer",
            10112: "VR 엔지니어",
            1022: "BI 엔지니어",
            894: "루비온레일즈 개발자",
            793: "CIO,Chief Information Officer"
        }
        self.tag2field_map = {
            "포지션 상세": "position_detail",
            "주요업무": "main_tasks",
            "자격요건": "qualifications",
            "우대사항": "preferred_qualifications",
            "혜택 및 복지": "benefits",
            "채용 전형": "hiring_process",
            "기술 스택 • 툴": "tech_stack",
            "마감일": "deadline"
        }

    def get_url_list(self) :
        filename = self.filenames["url_list"]
        driver = self.driver()

        job_dict = {}
        if os.path.exists(filename):
            with open(filename) as f:
                job_dict = json.load(f)
        
        for job_category in self.job_category_id2name:
            if job_category in job_dict:
                continue

            driver.get(f"{self.endpoint}/wdlist/{self.job_parent_category}/{job_category}")

            page_source = self.scroll_down_page(driver)

            soup = BeautifulSoup(page_source, 'html.parser')
            ul_element = soup.find('ul', {'data-cy': 'job-list'})
            position_list = [
                a_tag['href'] for a_tag in ul_element.find_all('a') if a_tag.get('href', '').startswith('/wd/')
            ]

            job_dict[job_category] = {
                "page_source": page_source,
                "position_list": position_list
            }

            with open(os.path.join(self.data_data, f"{self.site_name}.url_list.json"))
                json.dump(job_dict, f)
            
        driver.close()

        return job_dict

    def get_recruit_content_info(self, job_dict=None):
        if job_dict is None:
            if os.path.exists(self.filenames['url_list']):
                with open(self.filenames["url_list"]) as f:
                    job_dict = json.load(f)
            else:
                job_dict = {}

        filename = self.filenames["content_info"]
        driver = self.driver()

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
                content_dict[position_url] = driver.page_source

            position_content_dict[job_category] = content_dict

            with open(os.path.join(self.data_path, f"{self.site_name}.content_info.json"), "w") as f:
                json.dump(position_content_dict, f)
            
            driver.close()

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

        for job_category, info_dict in position_content_dict.items():
            for url, content in info_dict.items():
                result = {
                    "url": f"{self.endpoint}{url}",
                    "job_category": job_category,
                    "job_name": self.job_category_id2name[int(job_category)]
                }

                soup = BeautifulSoup(content, 'html')

                job_header = soup.find("section", class_="JobHeader_className__HttDA")

                try:
                    result['title'] = job_header.find("h2").text
                except AttributeError:
                    continue

                _company_info = job_header.find("span", class_="JobHeader_companyNameText__uuJyu")
                result['company_name'] = _company_info.text
                result['company_id'] = _company_info.find("a")["href"]

                _tag_list = job_header.find("div", class_="Tags_tagsClass__mvehZ").find_all("a")
                result['tag_name'] = [tag.text.lstrip("#") for tag in _tag_list]
                result['tag_id'] = [tag["href"] for tag in _tag_list]

                job_body = soup.find("section", class_="JobDescription_JobDescription__VWfcb")

                p_tags = job_body.find_all("p")
                h3_tags = job_body.find_all("h3")

                for i, p_tag in enumerate(p_tags):
                    h3_tag = h3_tags[i - 1].text if i != 0 else "설명"
                    if h3_tag not in self.tag2field_map:
                        continue

                    field_name = self.tag2field_map[h3_tag]
                    if field_name == "tech_list":
                        result[field_name] = [
                            skill.text for skill in p_tag.find("div").find_all("div")
                        ]
                    else:
                        result[field_name] = [
                            line for lines in p_tag.text.split("<br>") for line in lines.split("• ") if line
                        ]

                postprocess_dict[url] = result
                file.write(json.dumps(result) + "\n")

        file.close()

        return postprocess_dict

    def update_postprocess(self, position_content_dict=None):
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
                    for section_div in section_divs:
                        h3 = section_div.find("h3", class_="wds-1y0suvb")
                        if h3:
                            section_title = h3.text.strip()
                            content_span = section_div.find("span", class_="wds-wcfcu3")
                            if content_span:
                                content_text = content_span.get_text(separator='\n').strip()
                                content_lines = [line.strip() for line in content_text.split('\n') if line.strip()]
                                if content_lines and content_lines[0].startswith('•'):
                                    items = [line.lstrip('• ').strip() for line in content_lines]
                                    detailed_content[self.map_section_to_field.get(section_title, section_title.lower().replace(" ", "_"))] = items
                                else:
                                    detailed_content[self.map_section_to_field.get(section_title, section_title.lower().replace(" ", "_"))] = content_text
                
                # Construct result
                result = {
                    "url": f"https://www.wanted.co.kr{url}",
                    "job_category": job_category,
                    "job_name": self.job_category_id2name.get(int(job_category), job_category),
                    "title": job_title,
                    "company_name": company_name,
                    "company_id": company_id,
                    "tag_name": tag_name_list,
                    "tag_id": tag_id_list,
                    **detailed_content
                }
                
                # Write to file
                file.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        file.close()

    def run(self):
        job_dict = self.get_url_list()
        position_content_dict = self.get_recruit_content_info(job_dict)
        #result_dict = self.postprocess(position_content_dict)
        result_dict = self.update_postprocess(position_content_dict)
        return result_dict
