from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re
import requests
import json

import pdf2doi
import os

import spacy
import pytextrank

pdf2doi.config.set("verbose", True)
target_path = os.getcwd() + "/public/pdf_temp"

chrome_path = "C:\\ProgramData\\Anaconda3\\chromedriver.exe"
options = webdriver.ChromeOptions()
options.page_load_strategy = "eager"
options.add_argument("headless")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
)
options.add_argument("--ignore-ssl-errors")
options.add_argument("--ignore-certificate-errors")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_argument("--disable-blink-features=AutomationControlled")


def open_APS_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.close()
    driver.quit()
    data = {
        "link": url,
        "title": "",
        "authors": [],
        "institutes": [],
        "DOI": "",
        "abstract": "",
        "date": "",
        "areas": [],
    }
    data["title"] = soup.select("h3")[0].text
    for author in soup.select(".authors .content p a"):
        if author.text:
            data["authors"].append(author.text)
    if soup.select(".authors .content ul"):
        for institute in soup.select(".authors .content ul")[0].select("li"):
            data["institutes"].append(re.sub(r"^\d", "", institute.text))
    data["DOI"] = soup.select(".doi-field")[0].text
    if soup.select(".abstract .content p"):
        data["abstract"] = soup.select(".abstract .content p")[0].text
    data["date"] = soup.find(attrs={"property": "article:published_time"}).attrs[
        "content"
    ]
    if soup.select(".physh-concepts"):
        for area in soup.select(".physh-concepts")[0].select(".physh-concept"):
            data["areas"].append(area.text)
    data["publication"] = data["DOI"].split("/")[-1].split(".")[0]
    return data


def open_ACS_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path))
    driver.get(url)
    title = driver.find_elements(By.CLASS_NAME, "hlFld-Title")[1].text.replace("\n", "")
    author = driver.find_element(By.CLASS_NAME, "loa").text.replace("\n", "")
    magazine = driver.find_element(By.CLASS_NAME, "cit-title").text
    try:
        abstract = driver.find_element(
            By.CLASS_NAME, "articleBody_abstractText"
        ).text.replace("\n", "")
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_Elsevier_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path))
    driver.get(url)
    title = driver.find_element(By.CLASS_NAME, "title-text").text.replace("\n", "")
    author_list = driver.find_elements(By.CLASS_NAME, "author.size-m.workspace-trigger")
    author = ""
    for i in range(len(author_list)):
        author += author_list[i].find_element(By.CLASS_NAME, "text.given-name").text
        author += " "
        author += author_list[i].find_element(By.CLASS_NAME, "text.surname").text
        if i != len(author_list) - 1:
            author += ","
    magazine = driver.find_element(
        By.CLASS_NAME, "article-branding.u-show-from-sm"
    ).get_attribute("alt")
    try:
        abstract = driver.find_element(By.CLASS_NAME, "abstract.author").text
        if abstract[:8].lower() == "abstract":
            abstract = abstract[8:].replace("\n", "")
        elif abstract[:7].lower() == "summary":
            abstract = abstract[7:].replace("\n", "")
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_Nature_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path))
    driver.get(url)
    title = driver.find_element(By.CLASS_NAME, "c-article-title").text.replace("\n", "")
    author = driver.find_element(
        By.XPATH, r'//ul [@data-test="authors-list"]'
    ).text.replace("\n", "")
    magazine = (
        driver.find_element(By.CLASS_NAME, "c-article-info-details")
        .find_element(By.TAG_NAME, "a")
        .text
    )
    try:
        abstract = driver.find_element(
            By.CLASS_NAME, "c-article-section__content"
        ).text.replace("\n", "")
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_RSC_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path))
    driver.get(url)
    title = driver.find_element(
        By.CLASS_NAME, "capsule__title.fixpadv--m"
    ).text.replace("\n", "")
    author_list = driver.find_elements(By.CLASS_NAME, "article__author-link")
    author = ""
    for i in range(len(author_list)):
        author += author_list[i].find_element(By.TAG_NAME, "a").text
        if i != len(author_list) - 1:
            author += ","
    magazine = driver.find_element(By.CLASS_NAME, "h--heading3.no-heading").text
    try:
        abstract = driver.find_element(By.CLASS_NAME, "capsule__text").text.replace(
            "\n", ""
        )
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_Science_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path))
    driver.get(url)
    title = (
        driver.find_element(By.CLASS_NAME, "core-container")
        .find_element(By.TAG_NAME, "h1")
        .text.replace("\n", "")
    )
    try:
        author_list = driver.find_element(
            By.CLASS_NAME, "authors.comma-separated"
        ).find_elements(By.XPATH, '//span[@property="author"]')
    except:
        author_list = driver.find_element(By.CLASS_NAME, "authors").find_elements(
            By.XPATH, '//span[@property="author"]'
        )
    author = ""
    for i in range(len(author_list)):
        author += author_list[i].find_element(By.TAG_NAME, "a").text
        if i != len(author_list) - 1:
            author += ","
    magazine = (
        driver.find_element(By.CLASS_NAME, "core-self-citation")
        .find_element(By.TAG_NAME, "div")
        .text
    )
    try:
        contain = driver.find_element(By.CLASS_NAME, "core-container")
        abstract = contain.find_element(
            By.XPATH, '//section[@id="abstract"]'
        ).text.split("\n")[1]
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_wiley_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path))
    driver.get(url)
    title = driver.find_element(By.CLASS_NAME, "citation__title").text.replace("\n", "")
    author_list = driver.find_element(By.CLASS_NAME, "accordion-tabbed").find_elements(
        By.TAG_NAME, "a"
    )
    author = ""
    for i in range(len(author_list)):
        author += author_list[i].text
        if i != len(author_list) - 1 and author_list[i].text != "":
            author += ","
    author = author[:-1]
    magazine = (
        driver.find_element(By.CLASS_NAME, "journal-banner-text")
        .find_element(By.TAG_NAME, "a")
        .text
    )
    try:
        abstract = driver.find_element(By.CLASS_NAME, "abstract-group").text
        if abstract[:8].lower() == "abstract":
            abstract = abstract[8:].replace("\n", "")
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_AIP_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.get(url)
    title = (
        driver.find_element(By.CLASS_NAME, "publicationHeader_title")
        .find_element(By.CLASS_NAME, "title")
        .text.replace("\n", "")
    )
    author_list = []
    author_list1 = driver.find_elements(By.CLASS_NAME, "contrib-author")
    for i in range(len(author_list1)):
        author_list.append(author_list1[i].find_elements(By.TAG_NAME, "a")[1].text)
    author = ",".join(author_list)
    magazine = driver.find_element(
        By.CLASS_NAME, "publicationContentCitation"
    ).text.split(";")[0]
    try:
        abstract = driver.find_element(
            By.CLASS_NAME, "abstractSection.abstractInFull"
        ).text
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def open_IOP_url(url):
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.get(url)
    title = driver.find_element(By.CLASS_NAME, "wd-jnl-art-title").text.replace(
        "\n", ""
    )
    author_list1 = driver.find_element(By.CLASS_NAME, "mb-0")
    author_list2 = author_list1.find_elements(By.XPATH, r'//span [@itemprop="name"]')
    author_list = []
    for i in range(len(author_list2)):
        author_list.append(author_list2[i].text)
    author = ",".join(author_list)
    magazine = driver.find_element(By.CLASS_NAME, "publication-title").text
    try:
        abstract = driver.find_element(
            By.CLASS_NAME, "article-text.wd-jnl-art-abstract.cf"
        ).text
    except:
        abstract = "\n"
    print(title, "\n", url, "\n", magazine, "\n", author, "\n", abstract)
    driver.close()
    driver.quit()


def get_url(url):
    if "doi.org/10.1103" in url or "aps.org" in url:
        return open_APS_url(url)
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
    result = pdf2doi.pdf2doi(target_path)[0]
    url = "https://dx.doi.org/" + result["identifier"]
    data = get_url(url)
    text = data["title"].lower() + ". " + data["abstract"].lower()
    keywords = extract_keywords(text)
    data["keywords"] = keywords
    print(json.dumps(data))
