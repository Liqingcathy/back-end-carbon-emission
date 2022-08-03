from ctypes import resize
from datetime import date, datetime
import itertools
import ssl
from attr import fields
from flask import Flask, Blueprint, jsonify
from requests import request
import requests
from bs4 import BeautifulSoup, Comment
import urllib.request
from elasticsearch_dsl import Search
from .elastic import es
from elasticsearch.helpers import bulk
import re

search_bp = Blueprint("search_bp", __name__)

#filter necessary text
def necessary_text(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]', 'a', 'h1', 'h2', 'link']:
        return False
    if isinstance(element, Comment):
        return False
    if re.match(r"[\n]+",str(element)): return False
    return True

def web_spider():
    response = requests.get(url='https://www.epa.gov/greenvehicles')
    response.encoding = 'GBK'
    soup_obj = BeautifulSoup(response.text, 'html.parser')

    records, all_li , text_res = [], [], []
    #pull all text from the specific class container
    all_divs = soup_obj.find_all(name='div', class_='l-grid l-grid--3-col')
    for div in all_divs:
        if not div.find(name='section', class_='usa-banner'):
            all_li += div.find_all(name='li')

    #from each title, parse each article from that link
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
        text_res.append({'title': title, 'url' : a_tag, 'content': text})
    # print(text_res)
    # exit()
    return text_res

# print(spider())

#create epa_info index and bulk save all title/url/content to elasticsearch db 
@search_bp.route('/green_vehicle', methods=['PUT'])
def create_spider_index():
    data_list = web_spider()
    res = bulk(es, data_list, index='epa_info')
    # bulk save list of JSON dict type fields to es db
    return jsonify(res[1])

#get request to server from db to return search query match from each content
@search_bp.route('/green_vehicle/<kw>', methods=['GET'])
def search_word(kw):
    print(f"kw {kw}")
    
    body = {
            "query": {
                "query_string": {
                    "fields": [
                        "title", "content"
                    ],
                    "query": kw
                }
            },
            "highlight": {
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"],
                "fields": {
                    "title": {
                        "fragment_size": 400,
                        "number_of_fragments": 2,
                        "no_match_size": 20
                    },
                    "content": {
                        "fragment_size": 400,
                        "number_of_fragments": 2,
                        "no_match_size": 20
                    }
                }
            }
        }
    
    # q = Search(using=es,  index='epa_info').query("match", content=kw) #.highlight("fields.title",fragment_size=50) # can do more .agg
    #keword query matches title or content or url
    q = es.search(index='epa_info', body=body)
    #q = Search(using=es,  index='epa_info').query("multi_match", query=kw, fields=['content', 'title', 'url'])
    #underhood query: {'query': {'match': {'title': keyword}}}
    # q = q.highlight('title').highlight('content')
    # print(q)  # serialize Search object to dict to display in console
    # res = q.execute()  
    all_hits = q['hits']['hits']
    print(f"search res_match_hit_length {len(all_hits)}")
    # _highlights = all_hits[1].meta.title
    
    # request_body = all_hits
    # for num, doc in enumerate(all_hits):
    #     #print("DOC ID:", doc["_id"], "---->", doc, type(doc), '\n')
    #     for key, value in doc.to_dict().items():
    #         print(key, "-->", value)

    #     print('\n\n')
    # print(res.to_dict())
    return (q)
