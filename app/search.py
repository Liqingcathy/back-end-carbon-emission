from datetime import date, datetime
from flask import Flask, Blueprint, jsonify
from requests import request
import requests
from bs4 import BeautifulSoup
from .elastic import es, es_bp, Search
search_bp = Blueprint("search_bp", __name__)


def spider():
    response = requests.get(url='https://www.epa.gov/greenvehicles')
    response.encoding = 'GBK'
    soup_obj = BeautifulSoup(response.text, 'html.parser')
    div_obj = soup_obj.find(name='div', class_='l-grid l-grid--3-col')

    li_list = div_obj.find_all(name='li')
    # debug for other li lists
    records = []
    for i in li_list:
        # print(i.find('a'))
        title = i.find(name='a').get_text()
        a_tag = 'https://www.epa.gov' + i.find('a').get('href')
        records.append({title: a_tag})
    return records
    # Automotive Trends Report https://www.epa.gov//automotive-trends


@es_bp.route('/green_vehicle', methods=['GET'])
def create_spider_index():
    titles = spider()
    # print(titles)
    body = {
        "title": "",
        "url": "",
        "date": datetime.now()
    }

    for t in titles:
        for key, val in t.items():
            body['title'] = key
            body['url'] = val
    print(es.get_source)
    print(es.index(index='epa_info', body=body))
    res = es.index(index='epa_info', body=body)
    # need to save this whole fields to es db,can't see it now
    return res['_index']

# 因为db里没有保存/显示 fields， 所以search query kw结果没有结果 debug
@es_bp.route('/green_vehicle/<kw>', methods=['GET'])
def search_word(kw):
    print(f"kw {kw}")
    q = Search(using=es,  index='epa_info').query("match", title=kw)  # can do more .agg
    #underhood query: {'query': {'match': {'title': keyword}}}
    
    print(q.to_dict())  # serialize Search object to dict to display in console
    res = q.execute()  # to send to es db

    # all_hits = res['hits']['hits']
    # print(f"search res_match_hit_length {len(all_hits)}")
    # # request_body = all_hits
    # for num, doc in enumerate(all_hits):
    #     print("DOC ID:", doc["_id"], "---->", doc, type(doc), '\n')

    #     for key, value in doc.to_dict().items():
    #         print(key, "-->", value)

    #     print('\n\n')
    print(res.to_dict())
    return (res.to_dict())
