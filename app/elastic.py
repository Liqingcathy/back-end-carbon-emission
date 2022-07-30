from asyncio.log import logger
from datetime import datetime
from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import bulk
from flask import Flask, Blueprint, jsonify
from requests import request
from .app import VEHICLE_MAKE_RES, USER_INPUT, VEHICLE_MODEL_RES, app
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

#localhost/9000/user displays user's emission estimation result
@es_bp.route('/user', methods=['GET'])
def estimation_result_by_user():
    res = es.index(index=idx, document=VEHICLE_MODEL_RES)
    print(res)
    return res['_index']

#localhost/9000/user/mpg loads csv file and search for matches
@es_bp.route('/user/mpg', methods=['GET'])
def user_emission_model_mpg():
    get_csv()
    print('after csv bulk loading, get index\n')
    # get_index()

    print('search index=user_name \n')
    res= search_index()
    return res['hits']['total']

#read csv file and bulk load to elasticsearch with given index=user_name
def get_csv():
    with open('app/data/fuel_economy_mpg_by_vehicle.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        bulk(es, reader, index=idx)


def get_index():
    res = es.get(index=idx, id='nmrKS4IBYWDwJZnf8ZAy')
    print(res['_source'])
    return res

#search all and specific field with query body: for now returns 10 doc.
def search_index():
    res_match_all = es.search(index=idx, query={"match_all": {}})
    print(f"search result-match all {res_match_all}")

    all_hits = res_match_all['hits']['hits']
    print(f"search res_match_hit_length {len(all_hits)}")
    #return only 10, but have 200+ in csv.file

    #iterate hits dict
    for num, doc in enumerate(all_hits):
        print("DOC ID:", doc["_id"], "---->", doc, type(doc), '\n')

        for key, value in doc.items():
            print(key, "-->" , value)

        print('\n\n')

    res_match_field = es.search(index=idx, query={"match": {"Model Name": "MONACO"}})
    print(f"search result-match MONACO {res_match_field}")
    return res_match_all

# @es_bp.route('/vhmake', methods=['GET'])
# def get_vehicle_make_data():
#     for data in VEHICLE_MAKE_RES:
#         print(data)
#         res = es.index(index='vechicle_brand',
#                        document=VEHICLE_MAKE_RES, body=data)
#         print(res)
#     return res['_index']

# def get_csv_data():
#     file_name = 'MPG&CO2by Manufacturer.csv'
#     file = open(file_name)
#     data = [line.split(',') for line in file]

#     file.close()
#     return data
