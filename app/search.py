
from asyncio.log import logger
from elasticsearch import Elasticsearch, TransportError
from flask import Flask, Blueprint, jsonify
from requests import request
from bs4 import BeautifulSoup, Comment
import urllib.request
from elasticsearch_dsl import Search
from .elastic import es
from elasticsearch.helpers import bulk
import requests
import ssl
import re
import os


search_bp = Blueprint("search_bp", __name__)

def necessary_text(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]', 'a', 'link']:
        return False
    if isinstance(element, Comment):
        return False
    if re.match(r"[\n]+", str(element)):
        return False
    return True


def web_spider():
    response = requests.get(url='https://www.epa.gov/greenvehicles')
    response.encoding = 'GBK'
    soup_obj = BeautifulSoup(response.text, 'html.parser')

    records, all_li, text_res = [], [], []
    # pull all text from the specific class container
    all_divs = soup_obj.find_all(name='div', class_='l-grid l-grid--3-col')
    for div in all_divs:
        if not div.find(name='section', class_='usa-banner'):
            all_li += div.find_all(name='li')

    # from each title, parse each article from that link
    for li in all_li:
        title = li.find(name='a').get_text()
        a_tag = 'https://www.epa.gov' + li.find('a').get('href')
        response2 = urllib.request.urlopen(
            a_tag, context=ssl._create_unverified_context()).read()
        soup_obj2 = BeautifulSoup(response2, 'html.parser')
        texts = soup_obj2.findAll(text=True)
        useful_texts = filter(necessary_text, texts)
        text = u",".join(t.strip() for t in useful_texts)
        text = text.lstrip().rstrip()

        records.append({title: a_tag})
        text_res.append({'title': title, 'url': a_tag, 'content': text})
    return text_res

# create epa_info index and bulk save all title/url/content to elasticsearch db
@search_bp.route('/green_vehicle', methods=['PUT'])
def create_spider_index():
    data_list = web_spider()
    if not es.indices.exists(index='epa_info'):
        res = bulk(es, data_list, index='epa_info')
    
    return jsonify(res[1])

# get request to server from db to return search query match from each content
@search_bp.route('/green_vehicle/<kw>', methods=['GET'])
def search_word(kw):
    body = {
        "query": {
            "query_string": {
                "fields": [
                    "title", "content"
                ],
                "query": kw
            }
        },

        #Trial for suggest keyword feature
        # "suggest": {
        #     "sug_1": {
        #         "text": kw,
        #         "term": {
        #             "field": "title",
        #         }
        #     },
        #     "sug_2": {
        #         "text": kw,
        #         "term": {
        #             "field": "content",
        #         }
        #     }
        # },
        
        #<em> highlight didn't work on UI
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
    
    q = es.search(index='epa_info', body=body)
    all_hits = q['hits']['hits']
    return (q)


    #Comment for record
    # q = Search(using=es,  index='epa_info').query("match", content=kw) #.highlight("fields.title",fragment_size=50) # can do more .agg
    # keyword query matches title or content or url
    #q = Search(using=es,  index='epa_info').query("multi_match", query=kw, fields=['content', 'title', 'url'])
    # underhood query: {'query': {'match': {'title': keyword}}}
    # q = q.highlight('title').highlight('content') #not working
    # res = q.execute()
