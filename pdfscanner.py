import json
import os
import re
import time
import traceback
from datetime import datetime
from sys import stderr

import pdf2doi
import pytextrank
import requests
import spacy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.wait import WebDriverWait

# pdf2doi配置项
pdf2doi.config.set("verbose", False)
pdf2doi.config.set("save_identifier_metadata", False)
pdf2doi.config.set("websearch", False)
target_path = os.getcwd() + "/public/pdf_temp"
# chrome配置项
chrome_path = "C:\\ProgramData\\Anaconda3\\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("headless")
options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("window-size=1920,3120")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--ignore-certificate-errors")
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

data = {
    "link": "",
    "title": "",
    "authors": [],
    "institutes": [],
    "DOI": "",
    "abstract": "",
    "date": "",
    "publication": "",
    "areas": [],
    "keywords": [],
}


def open_APS_url(url):
    # resp = requests.get(url)
    # soup = BeautifulSoup(resp.text, "lxml")
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select("h3")[0].text
        for author in soup.select(".authors .content p a"):
            if author.text:
                data["authors"].append(author.text)
        if soup.select(".authors .content ul"):
            for institute in soup.select(".authors .content ul")[0].select("li"):
                data["institutes"].append(re.sub(r"^\d", "", institute.text))
        data["DOI"] = soup.select(".doi-field")[0].text
        data["abstract"] = soup.select(".abstract .content p")[0].text
        data["date"] = soup.find(attrs={
            "property": "article:published_time"
        }).attrs["content"]
        if soup.select(".physh-concepts"):
            for area in soup.select(".physh-concepts")[0].select(".physh-concept"):
                data["areas"].append(area.text)
        data["publication"] = soup.select("h2")[0].text
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())


def open_ACS_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(1)
    try:
        driver.find_element(
            By.XPATH, "//*[@id='pb-page-content']/div/main/article/div[2]/div/div[2]/div/div/div[1]/div[4]/div[2]/div/div/div/ul/*/a/i").click()
    except:
        pass
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select(".hlFld-Title")[0].text
        for author in soup.select(".hlFld-ContribAuthor"):
            if author.text:
                data["authors"].append(author.text)
        # 机构为二重数组，每个人对应一个数组表示机构
        for institute in soup.select(".loa-info-affiliations"):
            arr = []
            for item in institute.select(".loa-info-affiliations-info"):
                arr.append(item.text)
            data["institutes"].append(arr)
        data["DOI"] = soup.select(".article_header-doiurl")[0].text
        data["abstract"] = soup.select(".articleBody_abstractText")[0].text
        date = soup.select(".pub-date-value")[0].text
        data["date"] = str(datetime.strptime(date, "%B %d, %Y")).split(" ")[0]
        for sub in soup.select(".rlist--inline.loa li>a"):
            if sub.text:
                data["areas"].append(sub.text)
        data["publication"] = soup.select(".cit-title")[0].text
        data["keywords"] = (soup.find(attrs={"name": "keywords"}).attrs["content"].split(","))
    except:
        stderr.write(traceback.format_exc())


def open_Elsevier_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(2)
    try:
        driver.find_element(By.ID, "show-more-btn").click()
    except:
        pass
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select(".title-text")[0].text
        for author in soup.select(".author.size-m.workspace-trigger"):
            full_name = (author.select(".given-name")[0].text + " " + author.select(".surname")[0].text)
            data["authors"].append(full_name)
        for institute in soup.select(".affiliation dd"):
            data["institutes"].append(institute.text)
        data["DOI"] = soup.select(".doi")[0].text
        abs = []
        for para in soup.select(".abstract.author div"):
            if para.select("h3"):
                abs.append(para.select("h3")[0].text)
            abs.append(para.select("p")[0].text)
        data["abstract"] = "\n".join(abs).replace("\xa0", " ")
        data["date"] = "-".join(soup.find(attrs={"name": "citation_publication_date"}).attrs["content"].split("/"))
        data["publication"] = soup.select(".publication-title-link")[0].text
        for keyword in soup.select(".keyword span"):
            data["keywords"].append(keyword.text)
    except:
        stderr.write(traceback.format_exc())


def open_Nature_url(url):
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select("h1")[0].text
        for author in soup.select(".c-article-author-list>li>a"):
            data["authors"].append(author.text)
        for institute in soup.select(".c-article-author-affiliation__address"):
            data["institutes"].append(institute.text)
        data["DOI"] = soup.select(
            ".c-bibliographic-information__list-item--doi .c-bibliographic-information__value")[0].text
        data["abstract"] = soup.select(".c-article-section__content")[0].text
        data["date"] = soup.select("time")[0].attrs["datetime"]
        data["publication"] = soup.select(".c-header__logo img")[0].attrs["alt"]
        if soup.select(".c-article-subject-list"):
            for subject in soup.select(".c-article-subject-list>li"):
                data["areas"].append(subject.text)
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())


def open_RSC_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(1)
    try:
        driver.find_element(By.ID, "btnAuthorAffiliations").click()
    except:
        pass
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select("title")[0].text.split("-")[0].strip()
        for author in soup.select(".article__author-link>a"):
            if len(author.text) > 1:
                data["authors"].append(author.text.replace("\n", " "))
        for institute in soup.select(".article__author-affiliation")[1:]:
            data["institutes"].append(institute.select("span")[1].text.split("E-mail")[0].replace("\n", "").strip())
        data["DOI"] = soup.select(".doi-link>dd")[0].text
        data["abstract"] = soup.select(".capsule__text")[0].text.replace("\n", "")
        for item in soup.select(".c.fixpadt--l"):
            if "First published" in item.text:
                date = item.select("dd")[0].text
        data["date"] = str(datetime.strptime(date, "%d %b %Y")).split(" ")[0]
        data["publication"] = soup.select(".h--heading3")[0].text
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())


def open_Science_url(url):
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select("h1")[0].text
        for author in soup.find_all(attrs={"name": "dc.Creator"}):
            data["authors"].append(author.attrs["content"].replace("\xa0", ""))
        # for institute in soup.select(".article__author-affiliation>span")[2:]:
        #     if institute.string:
        #         data["institutes"].append(institute.string.replace("\n", "").strip())
        # 点击展开，每个人分别对应一栏机构
        data["DOI"] = soup.select(".doi>a")[0].attrs["href"]
        data["abstract"] = soup.select("#abstract>div")[0].text
        date = soup.find(attrs={"property": "datePublished"}).text
        data["date"] = str(datetime.strptime(date, "%d %b %Y")).split(" ")[0]
        data["publication"] = soup.select(".core-self-citation span")[0].text
        data["areas"].append(soup.select(".meta-panel__overline")[0].text)
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())


def open_wiley_url(url):
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select(".citation__title")[0].text
        for author in soup.select(".loa .author-name>span"):
            data["authors"].append(author.text)
        # for institute in soup.select(".author-info"):
        #     arr=[]
        #     for item in institute.select("p")[1:]:
        #         arr.append(item.text)
        #     data["institutes"].append(arr)
        # 点击展开，每个人分别对应一栏机构，可直接在页面源码获得
        data["DOI"] = soup.select(".epub-doi")[0].text
        data["abstract"] = (soup.select(".article-section__content.main")
                            [0].text.replace("\xa0", " ").replace("\n", ""))
        date = soup.select(".epub-date")[0].text
        data["date"] = str(datetime.strptime(date, "%d %B %Y")).split(" ")[0]
        data["publication"] = soup.select(".pb-dropzone img")[0].attrs["alt"]
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())


def open_AIP_url(url):
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(1)
    try:
        driver.find_element(By.ID, "affiliations").click()
    except:
        pass
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select(".publicationHeader_title>li")[0].text
        for author in soup.select(".entryAuthor>span>a"):
            if(author.text):
                data["authors"].append(author.text.strip())
        for institute in soup.select(".author-affiliation"):
            data["institutes"].append(re.sub(r"^\d", "", institute.text))
        data["DOI"] = soup.select(".publicationContentCitation>a")[0].text
        data["abstract"] = soup.select(".NLM_paragraph")[0].text
        date = soup.select(".dates")[-1].text.split("Published Online: ")[1].strip()
        data["date"] = str(datetime.strptime(date, "%d %B %Y")).split(" ")[0]
        data["publication"] = soup.select(".header-journal-title")[0].text
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())

    # title = (driver.find_element(By.CLASS_NAME, "publicationHeader_title").find_element(
    #     By.CLASS_NAME,
    #     "title").text.replace("\n", ""))
    # author_list = []
    # author_list1 = driver.find_elements(By.CLASS_NAME, "contrib-author")
    # for i in range(len(author_list1)):
    #     author_list.append(author_list1[i].find_elements(By.TAG_NAME,
    #                                                      "a")[1].text)
    # author = ",".join(author_list)
    # magazine = driver.find_element(
    #     By.CLASS_NAME, "publicationContentCitation").text.split(";")[0]
    # try:
    #     abstract = driver.find_element(By.CLASS_NAME,
    #                                    "abstractSection.abstractInFull").text
    # except:
    #     abstract = "\n"
    # print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    # driver.close()
    # driver.quit()


def open_IOP_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.get(url)
    title = driver.find_element(By.CLASS_NAME,
                                "wd-jnl-art-title").text.replace("\n", "")
    author_list1 = driver.find_element(By.CLASS_NAME, "mb-0")
    author_list2 = author_list1.find_elements(By.XPATH,
                                              r'//span [@itemprop="name"]')
    author_list = []
    for i in range(len(author_list2)):
        author_list.append(author_list2[i].text)
    author = ",".join(author_list)
    magazine = driver.find_element(By.CLASS_NAME, "publication-title").text
    try:
        abstract = driver.find_element(
            By.CLASS_NAME, "article-text.wd-jnl-art-abstract.cf").text
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def get_url(url):
    if "doi.org/10.1103" in url or "aps.org" in url:
        open_APS_url(url)
    elif "doi.org/10.1021" in url or "acs.org" in url:
        open_ACS_url(url)
    elif "doi.org/10.1016" in url or "sciencedirect.com" in url:
        open_Elsevier_url(url)
    elif "doi.org/10.1038" in url or "nature.com" in url:
        open_Nature_url(url)
    elif "doi.org/10.1039" in url or "pubs.rsc.org" in url:
        open_RSC_url(url)
    elif "doi.org/10.1126" in url or "science.org" in url:
        open_Science_url(url)
    elif "doi.org/10.1002" in url or "wiley.com" in url:
        open_wiley_url(url)
    elif "doi.org/10.1063" in url or "aip.scitation.org" in url:
        open_AIP_url(url)
    elif "doi.org/10.1149" in url or "iop.org" in url:
        open_IOP_url(url)


def extract_keywords(text):
    # 导入模块en_core_web_lg
    nlp = spacy.load("en_core_web_lg")
    # add PyTextRank to the spaCy pipeline
    nlp.add_pipe("positionrank")
    doc = nlp(text)
    keywords = []
    for phrase in doc._.phrases:
        if len(phrase.text.split(" ")) > 1 and len(keywords) < 5:
            keywords.append(phrase.text)
    return keywords


if __name__ == "__main__":
    # url = "https://aip.scitation.org/doi/full/10.1063/5.0099590"
    # start_time = datetime.now()
    # get_url(url)
    # end_time = datetime.now()
    # print(data)
    # print(end_time - start_time)
    result = pdf2doi.pdf2doi(target_path)[0]
    url = "https://dx.doi.org/" + result["identifier"]
    get_url(url)
    print(json.dumps(data))
