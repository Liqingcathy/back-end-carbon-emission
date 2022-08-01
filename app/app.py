from werkzeug.wrappers.json import JSONMixin
from flask import Flask, Blueprint, request, jsonify, make_response
import os
from dotenv import load_dotenv
import requests
load_dotenv()


car_bp = Blueprint("car_bp", __name__)
carbon_key = os.environ.get("CARBON_INTF_API_KEY")

app = Flask(__name__)
# header for carbon api
HEADER = {'Authorization': f'Bearer {carbon_key}',
          'Content-Type': 'application/json'
          }

VEHICLE_MAKE_RES = {}
VEHICLE_MODEL_RES = {}
USER_INPUT = {}
SEARCH_KW = None
# get model id to request estimation result


@ car_bp.route('/vehicle_makes/<id>/vehicle_models', methods=['GET'])
def get_vehicle_model_id(id):
    '''data: vehicle_model_id,vehicle_model_name, vehicle_brand_name(limited to 4), year '''
    print('inside get model id func')
    vehicle_model_id = None
    url = f"https://www.carboninterface.com/api/v1/vehicle_makes/{id}/vehicle_models"
    model_list = requests.get(url, headers=HEADER).json()

    for i in range(len(model_list)):
        # print(f"model_list[i] {model_list[i]}")
        for val in model_list[i].values():
            vehicle_model_id = val['id']
            # print(vehicle_model_id)

    return vehicle_model_id

# calls from frontend to create user's estimation result


@ car_bp.route('/estimate', methods=['POST', 'GET'])
def create_estimated_val():
    print('estimate post request')

    # list_makes = get_vehicle_makes()
    list_makes = (requests.get(
        'https://www.carboninterface.com/api/v1/vehicle_makes', headers=HEADER)).json()
    VEHICLE_MAKE_RES = list_makes

    request_body = request.get_json()
    vehicle_make_id = None
    # get vehicle make id by calling api func
    for i in range(len(list_makes)):
        for val in list_makes[i].values():
            if request_body['brand_name'] == val['attributes']['name']:
                vehicle_make_id = val['id']

    vehicle_model_id = None
    vehicle_model_id = get_vehicle_model_id(vehicle_make_id)

    request_body['vehicle_model_id'] = vehicle_model_id
    print(f"ready to post request {request_body}")
    USER_INPUT = request_body

    response = requests.post(
        'https://www.carboninterface.com/api/v1/estimates', headers=HEADER, json=request_body)
    VEHICLE_MODEL_RES = response.json()
    return response.json(), 201


@ app.route('/vehicles', methods=['POST'])
def get_search_words():
    print('try get event keyword')
    SEARCH_KW = requests.get('https://api.github.com/events')
    print(SEARCH_KW)
    response = requests.post(
        'http://127.0.0.1:9000/user/search-dsl', json=SEARCH_KW)
    return response.json(), 201





if __name__ == '__main__':

    app.run(port=9000, debug=True)
