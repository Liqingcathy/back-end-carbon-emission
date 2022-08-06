
import json
from time import time
from flask import Flask, Blueprint, request, jsonify, make_response
import os
from dotenv import load_dotenv
import app
# from .app import create_app
from .elastic import es
import requests

load_dotenv()


car_bp = Blueprint("car_bp", __name__)
carbon_key = os.environ.get("CARBON_INTF_API_KEY")

# app = create_app()

# header for carbon api
HEADER = {'Authorization': f'Bearer {carbon_key}',
          'Content-Type': 'application/json'}

# get model id to request estimation result


@ car_bp.route('/vehicle_makes/<id>/vehicle_models', methods=['GET'])
def get_vehicle_model_id(id):
    '''data: vehicle_model_id,vehicle_model_name, vehicle_brand_name(limited to 4), year '''
    print('inside get model id func')
    url = f"https://www.carboninterface.com/api/v1/vehicle_makes/{id}/vehicle_models"
    model_list = requests.get(url, headers=HEADER).json()

    print(len(model_list))
    return model_list
# calls from frontend to create user's estimation result


@ car_bp.route('/estimate', methods=['POST', 'GET'])
def create_estimated_val():
    print('estimate post request')

    # list_makes = get_vehicle_makes()
    list_makes = (requests.get(
        'https://www.carboninterface.com/api/v1/vehicle_makes', headers=HEADER)).json()
    request_body = request.get_json()
    vehicle_make_id = None
    # get vehicle make id by calling api func
    for i in range(len(list_makes)):
        for val in list_makes[i].values():
            if request_body['brand_name'] == val['attributes']['name']:
                vehicle_make_id = val['id']

    vehicle_model_id = None
    print(request_body)
    vehicle_model_list = get_vehicle_model_id(vehicle_make_id)
    for i in range(len(vehicle_model_list)):
        for val in vehicle_model_list[i].values():
            if val['attributes']['name'] == request_body['model_name']:
                if int(val['attributes']['year']) == int(request_body['year']):
                    vehicle_model_id = val['id']
                    break
                    #vehicle_name = val['attributes']['name']
                    #print(f'model and id match? {vehicle_model_id} {vehicle_name}')

    print(f"vehicle_model_id {vehicle_model_id}")
    request_body['vehicle_model_id'] = vehicle_model_id

    response = requests.post(
        'https://www.carboninterface.com/api/v1/estimates', headers=HEADER, json=request_body)

    if response:
        print(
            f"response {response.json()['data']['attributes']['carbon_g']}")

        request_body['emission'] = response.json(
        )['data']['attributes']['carbon_g']
        request_body['emission_per_mile'] = (
            int(request_body['emission']) // int(request_body['distance_value']))
        print(f"ready to store in es db {request_body}")

        verify_name = request_body['user_name']
        # verify duplication of user name before creating new record
        res = es.search(index='user_input', body=json.dumps(
            {"query": {"match_phrase": {"user_name": verify_name}}}))  # exact search

        if len(res['hits']['hits']) == 0:
            print("create id when not exists")
            es.index(index='user_input', body=request_body)
    print(response.json())
    return response.json(), 201


# @app.route('/')
# def hello():
#     return 'Welcome to Carbon emission server'


# if __name__ == '__main__':
#     # app.run()

#     # app.run(port=5000, debug=True)
#     app.run(host='0.0.0.0', port=5000, debug=True)
