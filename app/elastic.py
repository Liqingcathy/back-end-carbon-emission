from datetime import datetime
import os
from typing import Counter
from attr import field
import certifi
from flask import Flask, Blueprint, jsonify
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl import Search, A
from elasticsearch.helpers import bulk
from elasticsearch_dsl.query import MultiMatch, Match
import csv
import json

from requests import request
# import scipy.io


es = Elasticsearch(
    cloud_id=os.environ.get('CLOUD_ID'),
    http_auth=(os.environ.get('CLOUD_USER'),
               os.environ.get('CLOUD_PW'))
)


es_bp = Blueprint("es_bp", __name__)

# save user's input


@es_bp.route('/user/<user_name>', methods=['GET'])
def search_user(user_name):
    print(type(user_name))
    # res = es.search(es, index='user_input',  query=kw)
    user_emission = es.search(index='user_input', body=json.dumps(
        {"query": {"match_phrase": {"user_name": user_name}}}))

    print(user_emission['hits']['hits'])
    return jsonify(user_emission['hits']['hits'])

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
                    },
                    {
                        "match": {
                            "trany": "Automatic"
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


# read csv file and bulk load to elasticsearch with given index=fuel_economy
@es_bp.route('/user/models_efficiency', methods=['PUT'])
def create_fuel_economy_index_from_csv_file():
    with open('app/data/vehicle_fuel_economy.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        if not es.indices.exists(index='model_mpg'):
            bulk(es, reader, index='model_mpg')

        return 'Success'


@es_bp.route('/popular_vehicle_model_search', methods=['GET'])
def popular_model_search():
    body_query = {
        "aggs": {
            "my_fields": {
                "terms": {
                    # "field": "brand_name.keyword",
                    "field": "model_name.keyword",
                    "size": 5
                }
            }
        }
    }

    #s = es.search(index='user_input', body={'query': {'match_all': {}}})
    # s['hits']['hits'] only returns 10 documents in elasticsearch, instead use dsl
    #s = Search(using=es, index="user_input")
    s = es.search(index='user_input', body=body_query)
    top_5_model = s['aggregations']['my_fields']['buckets']
    result = []
    for obj in s['hits']['hits']:
        for model in top_5_model:
            if model['key'] in obj['_source']['model_name']:
                result.append(obj)

    # s.execute()
    # print(s['hits']['hits'])  # brand name associated with top 3 model name
    # print(s['aggregations']['my_fields']['buckets'])  # unique top 3 model name
    # print(result)
    # return jsonify(s['aggregations']['my_fields']['buckets'])
    return jsonify(result)


@es_bp.route('/popular_vehicle_make_search', methods=['GET'])
def popular_make_search():
    body_query = {
        "aggs": {
            "my_fields2": {
                "terms": {
                    "field": "brand_name.keyword",
                    "size": 5
                }
            }
        }
    }
    s = es.search(index='user_input', body=body_query)
    top_5_make = s['aggregations']['my_fields2']['buckets']
    print(top_5_make)

    result = []
    for obj in s['hits']['hits']:
        for make in top_5_make:
            if make['key'] == obj['_source']['brand_name']:
                # if result.get(make['key']) not in result.values():
                #     result[make['key']] = [obj]
                # else:
                #     result.get(make['key']).append(obj)
                result.append(obj)
    print(result)
    # debug to return mini, frontend return 8 objects, should return
    return jsonify(result)

# get a specific user's vehicle make name and filter models
# with similar mpg range, fuel-cost oil consumption


@es_bp.route('/same_make_diff_model/<make_kw>', methods=['GET'])
def same_make_diff_model(make_kw):
    print(make_kw)  # Toyota-Corolla-28

    splitKW = make_kw.split('-')
    make, model, mpg = splitKW[0], splitKW[1], str(splitKW[2])

    body_query = {
        # "size": 5000, #to return full 60 list
        "query": {
            "bool": {
                "must": [
                    {"match":
                        {"make": make}},
                    {"match":
                        {"combMPGSF": mpg}},
                ]
            }
        },
        "aggs": {
            "getModelsWithSameMpg": {
                "terms": {
                    "field": "model.keyword",
                    "size": 20
                }
            }
        }
    }

    similar_models = es.search(index='model_mpg', body=body_query)
    # print(similar_models['hits']['hits'])
    model_list_ten = similar_models['aggregations']['getModelsWithSameMpg']['buckets']
    print(len(similar_models['hits']['hits']))
    # print(similar_models['hits']['hits'])
    print(len(model_list_ten))
    # print(f"filted 10 model_list with same make, mpg {model_list_ten}")

    return jsonify(similar_models['hits']['hits'])
    # return jsonify(similar_models['hits']['hits'])

# search doc matches same given mpg, and filter all models from different makes, with less oil consume?

# tailpipe CO2 in grams/mile for vs emission permile
# kw should be model-mpg-emissionpermile


@es_bp.route('/same_model_diff_make_model/<model_kw>', methods=['GET'])
def same_model_fuel_economy(model_kw):
    splitKW = model_kw.split('-')
    make, model, mpg, emissionPermile = splitKW[0], splitKW[1], str(
        splitKW[2]), str(splitKW[3])

    body_query = {
        "size": 30,  # to return full 60 list
        "query": {
            "bool": {
                "must": [
                    {"match":
                        {"combMPGSF": mpg}},
                ],
                "must_not": [
                    {
                        "term": {
                            "model": model
                        }
                    },
                    {
                        "term": {
                            "make": make
                        }
                    }
                ]
            }
        },
        "aggs": {
            "model_mpg_emission": {
                "terms": {
                    "field": "model.keyword",
                    "size": 30
                }
            }
        }
    }
    similar_models = es.search(index='model_mpg', body=body_query)
    # print(similar_models['hits']['hits'])
    model_list_ten = similar_models['aggregations']['model_mpg_emission']['buckets']
    print(len(similar_models['hits']['hits']))
    print(model_list_ten)

    return jsonify(similar_models['hits']['hits'])
