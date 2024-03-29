from datetime import datetime
from flask import Flask, Blueprint, jsonify
from requests import request
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl import Search, A
from elasticsearch.helpers import bulk
from elasticsearch_dsl.query import MultiMatch, Match
from typing import Counter
from attr import field
import certifi
import csv
import json
import os



es = Elasticsearch(
    cloud_id=os.environ.get('CLOUD_ID'),
    http_auth=(os.environ.get('CLOUD_USER'),
               os.environ.get('CLOUD_PW'))
)


es_bp = Blueprint("es_bp", __name__)

@es_bp.route('/user/<user_name>', methods=['GET'])
def search_user(user_name):
    user_emission = es.search(index='user_input', body=json.dumps(
        {"query": {"match_phrase": {"user_name": user_name}}}))
    return jsonify(user_emission['hits']['hits'])

# @es_bp.route('/user/models', methods=['GET'])
def create_user_models_index():
    if not es.indices.exists(index='user_models'):
        res = es.index(index='user_models', document={})
    return jsonify(res)

# retrieve current user's model info and compare with others emission and mp
@es_bp.route('/user/models_efficiency/<kw_model_year>', methods=['PUT'])
def get_fuel_efficiency(kw_model_year):
    kw_model_year = kw_model_year.split('-')
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
    # two kw in multiple fields --> model and year from model, and year fields
    req_mpg = es.search(index='model_mpg', body=query_body)
    return jsonify(req_mpg['hits']['hits'])


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

    s = es.search(index='user_input', body=body_query)
    top_5_model = s['aggregations']['my_fields']['buckets']
    result = []
    for obj in s['hits']['hits']:
        for model in top_5_model:
            if model['key'] in obj['_source']['model_name']:
                result.append(obj)

    #s['aggregations']['my_fields']['buckets']) unique top 3 model name
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

    result = []
    for obj in s['hits']['hits']:
        for make in top_5_make:
            if make['key'] == obj['_source']['brand_name']:
                result.append(obj)
    return jsonify(result)

# get a specific user's vehicle make name and filter models
# with similar mpg range, fuel-cost oil consumption
@es_bp.route('/same_make_diff_model/<make_kw>', methods=['GET'])
def same_make_diff_model(make_kw):
    splitKW = make_kw.split('-')
    make, model, mpg = splitKW[0], splitKW[1], str(splitKW[2])

    body_query = {
        # "size": 5000, to return full 60 list
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
    model_list_ten = similar_models['aggregations']['getModelsWithSameMpg']['buckets']
    return jsonify(similar_models['hits']['hits'])

# search doc matches same given mpg, and filter all models from different makes, with less oil consume
# tailpipe CO2 in grams/mile for vs emission permile
# kw provided by UI should be model-mpg-emissionpermile
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
    model_list_ten = similar_models['aggregations']['model_mpg_emission']['buckets']
    return jsonify(similar_models['hits']['hits'])
