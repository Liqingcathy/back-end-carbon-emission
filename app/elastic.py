from asyncio.log import logger
from datetime import datetime
from elasticsearch import Elasticsearch, TransportError, ElasticsearchException
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch, Match
from flask import Flask, Blueprint, jsonify
from requests import request
from .app import VEHICLE_MAKE_RES, USER_INPUT, VEHICLE_MODEL_RES, app
from .app import SEARCH_KW
import os
import csv

# initialize elasticsearch modules and get connection(reset password)
try:
    es = Elasticsearch("https://localhost:9200",
                       ca_certs=False,
                       verify_certs=False,
                       #ca_certs= os.environ.get('ES_CERT'),
                       http_auth=(os.environ.get('ES_USER'), os.environ.get('ES_PW')))
except (Exception, TransportError) as exception:
    logger.info("Error in connecting to ES cluster: {}".format(exception))

es_bp = Blueprint("es_bp", __name__)
idx = 'user_name'

# localhost/9000/user displays user's emission estimation result
@es_bp.route('/user/<kw>', methods=['GET'])
def create_user_search(kw):
    
    print("inside of search user keyword '\n")
    # hits hits _source model name = keyword
    q = Search(using=es,  index=idx).query("match", Manufacturer=kw)  # can do more .agg
    # serialize Search object to dict to display in console
    print(q.to_dict())  # {'query': {'match': {'title': keyword}}}

    res = q.execute()  # to send request to elasticsearch
    print(f"total hit {res.hits.total.value} \n")
    car_list = []
    if res:
        for hit in res:
            car_list.append(hit.to_dict())
            print(hit.to_dict())
    print(f"\ncar list {car_list}\n")
    return jsonify(car_list, 201)


@es_bp.route('/user', methods=['GET'])
def estimation_result_by_user():
    res = es.index(index=idx, document=VEHICLE_MODEL_RES)
    print(res)
    return res['_index']

# localhost/9000/user/mpg loads csv file and search for matches
@es_bp.route('/user/mpg', methods=['GET'])
def user_emission_model_mpg():
    print('inside of /user/mpg route')
    get_csv()
    print('after csv bulk loading, get index\n')
    # get_index()

    print('search index=user_name \n')
    res = search_mpg_match_all()
    return res['hits']['total']

# read csv file and bulk load to elasticsearch with given index=user_name


def get_csv():
    with open('app/data/fuel_economy_mpg_by_vehicle.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        bulk(es, reader, index=idx)


# search all and specific field with query body: for now returns 10 doc.
def search_mpg_match_all():
    res_match_all = es.search(index=idx, query={"match_all": {}})
    print(f"search result-match all {res_match_all}")

    all_hits = res_match_all['hits']['hits']
    print(f"search res_match_hit_length {len(all_hits)}")
    # return only 10, but have 200+ in csv.file

    # iterate hits dict
    for num, doc in enumerate(all_hits):
        print("DOC ID:", doc["_id"], "---->", doc, type(doc), '\n')

        for key, value in doc.items():
            print(key, "-->", value)

        print('\n\n')
    return res_match_all