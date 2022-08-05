from datetime import datetime
from flask import Flask, Blueprint, jsonify
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch.helpers import bulk
from elasticsearch_dsl.query import MultiMatch, Match
import csv
import json


with open('config.json') as json_data_file:
    config = json.load(json_data_file)
    
es = Elasticsearch(
    cloud_id = config['elasticsearch']['cloud_id'],
    api_key=(config['elasticsearch']['api_key'], config['elasticsearch']['api_key_secret'])
)
es.info()


es_bp = Blueprint("es_bp", __name__)

#save user's input
@es_bp.route('/user/<kw>', methods=['GET'])
def search_user_input(kw):
    # res = es.search(es, index='user_input',  query=kw)
    res = Search(using=es,  index='user_input').query("multi_match", query=kw, fields=['brand_name', 'model_name', 'user_name'])
    print(type(res))
    return jsonify(res.to_dict())

#save user's model response
#@es_bp.route('/user/models', methods=['GET'])
def create_user_models_index():
    if not es.indices.exists(index='user_models'):
        res = es.index(index='user_models', document={})
    print(res)
    return jsonify(res)

# retrieve model info based user's model info:
##FRONT-END 1: display same makes different models emission estimation comparision
@es_bp.route('/user/models/<kw>', methods=['GET'])
def search_user_model(kw):
    print("inside of search user keyword '\n")
    # hits hits _source model name = keyword
    q = Search(using=es,  index='same_make_models').query("multi_match", query=kw, fields=['data.attributes.vehicle_make', 'data.attributes.name', 'data.attributes.year'])  # can do more .agg
    #q = es.search(es, index='same_make_models', name=kw)
    # serialize Search object to dict to display in console
    print(q.to_dict())  # {'query': {'match': {'title': keyword}}}
    res = q.execute()  # to send request to elasticsearch
    print(f"total hit {res.hits.total.value} \n")
    # car_list = []
    # if res:
    #     for hit in res:
    #         car_list.append(hit.to_dict())
    #         print(hit.to_dict())
    # print(f"\ncar list {car_list}\n")

    # list_model_based_on_user_make = []
    #add list of models into the list and request emission post request together
    print(type(res))
    return jsonify(res['hits'], 201)

# #create fuel_economy index for later search
# @es_bp.route('/user/models/mpg', methods=['GET'])
# def create_user_models_mpg_index():
#      if not es.indices.exists(index='fuel_economy'):
#         res = es.index(index='fuel_economy', document=USER_INPUT)
#     print(res)
#     return jsonify(res)

# retrieve model mpg data from database
# @es_bp.route('/user/models/mpg', methods=['GET'])
# def user_emission_model_mpg():
#     print('inside of /user/models/mpg route')
#     # get_csv()
#     print('search index=user_name \n')
#     res = search_mpg_match_all()
    
#     return jsonify(res['hits']['hits'])

# read csv file and bulk load to elasticsearch with given index=user_name
@es_bp.route('/user/models/mpg', methods=['PUT'])
def create_fuel_economy_index_from_csv_file():
    with open('app/data/fuel_economy_mpg_by_vehicle.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        if not es.indices.exists(index='fuel_economy'):
            bulk(es, reader, index='fuel_economy')
        
        return 'Success'
# search all and specific field with query body: for now returns 10 doc.\
#FRONT-END 2: use the url to display in frontend
@es_bp.route('/user/models/mpg/<kw>', methods=['GET'])
def search_mpg_match_all(kw):
    
    # res_match_all = es.search(index='fuel_economy', query={"match_all": {}})
    q = Search(using=es,  index='fuel_economy').query("multi_match", query=kw, fields=['Manufacturer', 'Model Name', 'Real-World MPG_City'])  # can do more .agg
    
    res = q.execute()
    print(f"search result-match all {res.to_dict()}")
    # print(f"search res_match_hit_length {len(all_hits)}")
    # return only 10, but have 200+ in csv.file

    # iterate hits dict
    # for num, doc in enumerate(all_hits):
    #     print("DOC ID:", doc["_id"], "---->", doc, type(doc), '\n')

    #     for key, value in doc.items():
    #         print(key, "-->", value)

    #     print('\n\n')
    # print(type(all_hits))
    return jsonify(res.to_dict()['hits']['hits'])


