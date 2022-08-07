from datetime import datetime
import os
import certifi
from flask import Flask, Blueprint, jsonify
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl import Search
from elasticsearch.helpers import bulk
from elasticsearch_dsl.query import MultiMatch, Match
import csv
import json
# import scipy.io


es = Elasticsearch(
    cloud_id=os.environ.get('CLOUD_ID'),
    http_auth=(os.environ.get('CLOUD_USER'),
               os.environ.get('CLOUD_PW'))
)


es_bp = Blueprint("es_bp", __name__)

# save user's input


@es_bp.route('/user/<kw>', methods=['GET'])
def search_user(kw):
    # res = es.search(es, index='user_input',  query=kw)
    res = Search(using=es,  index='user_input').query("multi_match", query=kw, fields=[
        'brand_name', 'model_name', 'user_name', 'emission'])
    print(type(res))
    return jsonify(res.to_dict())

# save user's model response
# @es_bp.route('/user/models', methods=['GET'])


def create_user_models_index():
    if not es.indices.exists(index='user_models'):
        res = es.index(index='user_models', document={})
    print(res)
    return jsonify(res)

# retrieve current user's model info and compare with others emission and mpg


@es_bp.route('/user/models_efficiency/<kw_model_year>', methods=['PUT'])
def get_fuel_efficiency(kw_model_year):
    print("inside of get_fuel_efficiency '\n")

    # get user's model name, mile, and emission data from user_input index selectively
    # print(es.search(index='user_input', filter_path=[
    #        'hits.hits.user_name', 'hits.hits.emission', 'hits.hits.emission_per_mile']))
    # print(es.search(index='user_input', filter_path=['hits.hits._*'])) get all user's all field

    # req_user = es.search(index='user_input', body=json.dumps(
    #     {"query": {"match_phrase": {"emission_per_mile": kw_model}}}))  # exact search
    # print(f" from user input db exact search {req_user['hits']['hits']}")

    kw_model_year = kw_model_year.split('-')
    print(kw_model_year)
    model = kw_model_year[0]
    year = kw_model_year[1]

    query_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "model": model
                        }
                    },
                    {
                        "match": {
                            "year": year
                        }
                    }
                ]
            }
        }
    }
    # two kw in multiple fields --> model and yearfrom model, year fields
    req_mpg = es.search(index='model_mpg', body=query_body)
    # one kw in multiple fields--> es.search(index="model_mpg", body={"query": {"multi_match": {"query": kw, "fields": ["name", "description"]}}})
    # one kw exact search req_user = es.search(index='user_input', body=json.dumps(
    #     {"query": {"match_phrase": {"emission_per_mile": kw_model}}}))

    print(len(req_mpg['hits']['hits']))
    return jsonify(req_mpg['hits']['hits'])


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

# read csv file and bulk load to elasticsearch with given index=fuel_economy


@es_bp.route('/user/models_efficiency', methods=['PUT'])
def create_fuel_economy_index_from_csv_file():
    with open('app/data/vehicle_fuel_economy.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        if not es.indices.exists(index='model_mpg'):
            bulk(es, reader, index='model_mpg')

        return 'Success'

# @es_bp.route('/user/global_micro', methods=['PUT'])
# def mat_file():
#     mat_data = scipy.io.loadmat('app/data/global_micro_2019.mat')
#     print(type(mat_data))
