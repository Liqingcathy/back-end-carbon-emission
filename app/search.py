from datetime import date, datetime
import ssl
from flask import Flask, Blueprint, jsonify
from requests import request
import requests
from bs4 import BeautifulSoup, Comment
import urllib.request
from elasticsearch_dsl import Search
from elastic import es
from elasticsearch.helpers import bulk
import re

search_bp = Blueprint("search_bp", __name__)

def necessary_text(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]', 'li', 'a', 'h1', 'h2', 'link']:
        return False
    if isinstance(element, Comment):
        return False
    if re.match(r"[\n]+",str(element)): return False
    return True

def spider():
    response = requests.get(url='https://www.epa.gov/greenvehicles')
    response.encoding = 'GBK'
    soup_obj = BeautifulSoup(response.text, 'html.parser')

    records, all_li , text_res = [], [], []
    #pull all text from the class container
    all_divs = soup_obj.find_all(name='div', class_='l-grid l-grid--3-col')
    for div in all_divs:
        if not div.find(name='section', class_='usa-banner'):
            all_li += div.find_all(name='li')

  
    for li in all_li:
        title = li.find(name='a').get_text()
        a_tag = 'https://www.epa.gov' + li.find('a').get('href')
        response2 = urllib.request.urlopen(a_tag, context=ssl._create_unverified_context()).read()
        soup_obj2 = BeautifulSoup(response2, 'html.parser')
        texts = soup_obj2.findAll(text=True)
        useful_texts = filter(necessary_text, texts) 
        text = u",".join(t.strip() for t in useful_texts)
        text = text.lstrip().rstrip()
        
        records.append({title: a_tag})
        text_res.append({title: text})
    # print(text_res)
    # exit()
    return text_res

print(spider())

@search_bp.route('/green_vehicle', methods=['PUT'])
def create_spider_index():
    titles_url = spider()
    
    data_list = []
    for dict_ele in titles_url:
        for key, val in dict_ele.items():
            if key not in dict_ele:
                data_list.append({
                    "title": key,
                    "url": val
                })
    # print(body)
    # res = es.index(index='epa_info', document=data_list)
    res = bulk(es, data_list, index='epa_info')
    # bulk save list of JSON dict type fields to es db

    return jsonify(res[1])

# 因为db里没有保存/显示 fields， 所以search query kw结果没有结果 debug
@search_bp.route('/green_vehicle/<kw>', methods=['GET'])
def search_word(kw):
    print(f"kw {kw}")
    q = Search(using=es,  index='epa_info').query("match", title=kw) #.highlight("fields.title",fragment_size=50) # can do more .agg
    #underhood query: {'query': {'match': {'title': keyword}}}
    print(q.to_dict())  # serialize Search object to dict to display in console
    res = q.execute()  
    
    all_hits = res['hits']['hits']
    print(f"search res_match_hit_length {len(all_hits)}")
    # request_body = all_hits
    # for num, doc in enumerate(all_hits):
    #     #print("DOC ID:", doc["_id"], "---->", doc, type(doc), '\n')
    #     for key, value in doc.to_dict().items():
    #         print(key, "-->", value)

    #     print('\n\n')
    print(res.to_dict())
    return (res.to_dict())
