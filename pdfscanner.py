import argparse
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

# 获取文件路径
defalut_path = os.getcwd() + "/public/pdf_temp"
parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, default=defalut_path)
args = parser.parse_args()
target_path = args.path

# pdf2doi配置项
pdf2doi.config.set("verbose", False)
pdf2doi.config.set("save_identifier_metadata", False)
pdf2doi.config.set("websearch", False)

# chrome配置项
chrome_path = "C:\\ProgramData\\Anaconda3\\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("headless")
options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("window-size=1920,3120")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
)
options.add_argument("--ignore-ssl-errors")
options.add_argument("--ignore-certificate-errors")
options.add_experimental_option(
    "excludeSwitches", ["enable-automation", "enable-logging"]
)

data = {
    "url": "",
    "DOI": "",
    "date": "",
    "publication": "",
    "title": "",
    "abstract": "",
    "authors": [],
    "keywords": [],
    "subjects": [],
    "fundings": [],
    "refs": [],
}


def open_APS_url(url):
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
        data["date"] = soup.find(attrs={"property": "article:published_time"}).attrs[
            "content"
        ]
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
            By.XPATH,
            "//*[@id='pb-page-content']/div/main/article/div[2]/div/div[2]/div/div/div[1]/div[4]/div[2]/div/div/div/ul/*/a/i",
        ).click()
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
        data["keywords"] = (
            soup.find(attrs={"name": "keywords"}).attrs["content"].split(",")
        )
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
            full_name = (
                author.select(".given-name")[0].text
                + " "
                + author.select(".surname")[0].text
            )
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
        data["date"] = "-".join(
            soup.find(attrs={"name": "citation_publication_date"})
            .attrs["content"]
            .split("/")
        )
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
            ".c-bibliographic-information__list-item--doi .c-bibliographic-information__value"
        )[0].text
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
            data["institutes"].append(
                institute.select("span")[1]
                .text.split("E-mail")[0]
                .replace("\n", "")
                .strip()
            )
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
        data["abstract"] = (
            soup.select(".article-section__content.main")[0]
            .text.replace("\xa0", " ")
            .replace("\n", "")
        )
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
            if author.text:
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


def open_IOP_url(url):
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(1)
    try:
        driver.find_element(By.CLASS_NAME, "reveal-trigger-label.d-ib").click()
    except:
        pass
    time.sleep(0.5)
    try:
        driver.find_element(By.ID, "wd-article-info-accordion").click()
    except:
        pass
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    try:
        data["link"] = url
        data["title"] = soup.select("h1")[0].text
        for author in soup.select(".mb-0 .nowrap>span"):
            data["authors"].append(author.text)
        for institute in soup.select(".wd-jnl-art-author-affiliations>.mb-05"):
            data["institutes"].append(
                re.sub(r"^\d", "", institute.text).replace("\n", "").strip()
            )
        data["DOI"] = soup.select(".wd-jnl-art-doi>p>a")[0].text
        data["abstract"] = soup.select(".article-text.wd-jnl-art-abstract.cf>p")[0].text
        date = soup.find(attrs={"itemprop": "datePublished"}).text
        data["date"] = str(datetime.strptime(date, "%d %B %Y")).split(" ")[0]
        data["publication"] = soup.select(".publication-title")[0].text.replace(
            "\n", ""
        )
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    except:
        stderr.write(traceback.format_exc())


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
    elif "doi.org/10.1088" in url or "doi.org/10.1149" in url or "iop.org" in url:
        open_IOP_url(url)


def extract_keywords(text):
    # 导入模块en_core_web_lg
    nlp = spacy.load("en_core_sci_lg")
    # add PyTextRank to the spaCy pipeline
    nlp.add_pipe("positionrank")
    doc = nlp(text)
    keywords = []
    for phrase in doc._.phrases:
        if len(phrase.text.split(" ")) > 1 and len(keywords) < 5:
            keywords.append(phrase.text)
    return keywords


def elsevier_api(identifier):
    url = f"https://api.elsevier.com/content/abstract/doi/{identifier}?&view=FULL"
    headers = {
        "X-ELS-APIKey": "d5ea4b9f6d926fdc23703e67bb770013",
        "Accept": "application/json",
    }
    res = requests.request("GET", url, headers=headers)
    if res.status_code != 200:
        return
    raw_data = res.json()["abstracts-retrieval-response"]
    try:
        data["url"] = "https://doi.org/" + identifier
        data["DOI"] = raw_data["coredata"]["prism:doi"]
        data["date"] = raw_data["coredata"]["prism:coverDate"]
        data["publication"] = raw_data["coredata"]["prism:publicationName"]
        data["title"] = raw_data["coredata"]["dc:title"]
        data["abstract"] = raw_data["coredata"]["dc:description"]
        affiliations = {
            af["@id"]: ", ".join(
                [af["affilname"], af["affiliation-city"], af["affiliation-country"]]
            )
            for af in raw_data["affiliation"]
        }
        for auth in raw_data["authors"]["author"]:
            if type(auth["affiliation"]) == dict:
                author = {
                    "name": auth["preferred-name"]["ce:given-name"]
                    + " "
                    + auth["preferred-name"]["ce:surname"],
                    "affiliation": [affiliations[auth["affiliation"]["@id"]]],
                    "email": "",
                    "id": "",
                }
            else:
                ids = [afid["@id"] for afid in auth["affiliation"]]
                author = {
                    "name": auth["preferred-name"]["ce:given-name"]
                    + " "
                    + auth["preferred-name"]["ce:surname"],
                    "affiliation": [affiliations[id] for id in ids],
                    "email": "",
                    "id": "",
                }
            data["authors"].append(author)
    except:
        stderr.write(traceback.format_exc())
    try:
        data["keywords"] = [
            word["$"] for word in raw_data["authkeywords"]["author-keyword"]
        ]
    except:
        text = data["title"].lower() + ". " + data["abstract"].lower()
        data["keywords"] = extract_keywords(text)
    try:
        data["subjects"] = [
            area["$"] for area in raw_data["subject-areas"]["subject-area"]
        ]
    except:
        pass
    try:
        fundinglist = raw_data["item"]["xocs:meta"]["xocs:funding-list"]["xocs:funding"]
        if type(fundinglist) == dict:
            if "xocs:funding-agency" in fundinglist:
                fund_sponsor = fundinglist["xocs:funding-agency"]
            else:
                fund_sponsor = fundinglist["xocs:funding-agency-matched-string"]
            if "xocs:funding-id" in fundinglist:
                if type(fundinglist["xocs:funding-id"]) == str:
                    fund_id = [fundinglist["xocs:funding-id"]]
                else:
                    fund_id = [id["$"] for id in fundinglist["xocs:funding-id"]]
            else:
                fund_id = []
            data["fundings"].append({"fund-sponsor": fund_sponsor, "fund-id": fund_id})
        else:
            for fundinfo in fundinglist:
                if "xocs:funding-agency" in fundinfo:
                    fund_sponsor = fundinfo["xocs:funding-agency"]
                else:
                    fund_sponsor = fundinfo["xocs:funding-agency-matched-string"]
                if "xocs:funding-id" in fundinfo:
                    if type(fundinfo["xocs:funding-id"]) == str:
                        fund_id = [fundinfo["xocs:funding-id"]]
                    else:
                        fund_id = [id["$"] for id in fundinfo["xocs:funding-id"]]
                else:
                    fund_id = []
                data["fundings"].append(
                    {"fund-sponsor": fund_sponsor, "fund-id": fund_id}
                )
    except:
        pass
    try:
        refs = raw_data["item"]["bibrecord"]["tail"]["bibliography"]["reference"]
        data["refs"] = [ref["ref-fulltext"] for ref in refs]
    except:
        pass


if __name__ == "__main__":
    result = pdf2doi.pdf2doi(target_path)
    elsevier_api(result["identifier"])
    print(json.dumps(data))
