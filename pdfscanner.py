import argparse
import json
import os
import traceback
from sys import stderr

import pdf2doi
import pytextrank
import requests
import spacy

# 获取文件路径
defalut_path = os.getcwd()
parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, default=defalut_path)
args = parser.parse_args()
target_path = args.path

# pdf2doi配置项
pdf2doi.config.set("verbose", False)
pdf2doi.config.set("save_identifier_metadata", False)
pdf2doi.config.set("websearch", False)

xstr = lambda s: s or ""


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
    data = {
        "url": "",
        "DOI": "",
        "date": "",
        "publication": "",
        "title": "",
        "abstract": "",
        "authors": [],
        "affiliations": [],
        "keywords": [],
        "subjects": [],
        "fundings": [],
        "refs": [],
    }
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
            af["@id"]: xstr(af["affilname"])
            + ", "
            + xstr(af["affiliation-city"])
            + ", "
            + xstr(af["affiliation-country"])
            for af in raw_data["affiliation"]
        }
        data["affiliations"] = [
            {
                "afid": af["@id"],
                "afname": xstr(af["affilname"])
                + ", "
                + xstr(af["affiliation-city"])
                + ", "
                + xstr(af["affiliation-country"]),
            }
            for af in raw_data["affiliation"]
        ]
        for auth in raw_data["authors"]["author"]:
            if isinstance(auth["affiliation"], dict):
                author = {
                    "name": auth["preferred-name"]["ce:given-name"]
                    + " "
                    + auth["preferred-name"]["ce:surname"],
                    "affiliation": [affiliations[auth["affiliation"]["@id"]]],
                    "email": "",
                    "id": "",
                }
            if isinstance(auth["affiliation"], list):
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
        if isinstance(fundinglist, dict):
            if "xocs:funding-agency" in fundinglist:
                fund_sponsor = fundinglist["xocs:funding-agency"]
            else:
                fund_sponsor = fundinglist["xocs:funding-agency-matched-string"]
            if "xocs:funding-id" in fundinglist:
                if isinstance(fundinglist["xocs:funding-id"], str):
                    fund_id = [fundinglist["xocs:funding-id"]]
                if isinstance(fundinglist["xocs:funding-id"], list):
                    fund_id = [id["$"] for id in fundinglist["xocs:funding-id"]]
            else:
                fund_id = []
            data["fundings"].append({"fund-sponsor": fund_sponsor, "fund-id": fund_id})
        if isinstance(fundinglist, list):
            for fundinfo in fundinglist:
                if "xocs:funding-agency" in fundinfo:
                    fund_sponsor = fundinfo["xocs:funding-agency"]
                else:
                    fund_sponsor = fundinfo["xocs:funding-agency-matched-string"]
                if "xocs:funding-id" in fundinfo:
                    if isinstance(fundinfo["xocs:funding-id"], str):
                        fund_id = [fundinfo["xocs:funding-id"]]
                    if isinstance(fundinfo["xocs:funding-id"], list):
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
    return data


if __name__ == "__main__":
    result = pdf2doi.pdf2doi(target_path)
    if isinstance(result, dict):
        data = elsevier_api(result["identifier"])
        print(json.dumps(data))
    if isinstance(result, list):
        data = [elsevier_api(r["identifier"]) for r in result]
        print(json.dumps(data))
