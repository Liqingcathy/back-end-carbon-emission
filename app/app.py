import json
from flask import Flask, Blueprint, request, jsonify, make_response
import os
from dotenv import load_dotenv
import requests

load_dotenv()

car_bp = Blueprint("car_bp", __name__)

carbon_key = os.environ.get("CARBON_INTF_API_KEY")

app = Flask(__name__)

HEADER = {
    'Authorization': f'Bearer {carbon_key}',
    'Content-Type': 'application/json'
}


# @car_bp.route('/vehicle_makes', methods=['GET'])
# def get_vehicle_makes():
#     print('backend vehicle makes request')
#     '''data(list of dict): vehicle_make_id, vehicle_brand_name(limited to 4), #of models '''
#     # if response.status_code != 204 and 'content-type' in response.headers and 'application/json' in response.headers['content-type']:
#     response = requests.get(
#         'https://www.carboninterface.com/api/v1/vehicle_makes', headers=HEADER)
#     # print('vehicle_make', response.json())
#     return response.json(), 200


vehicle_model_id = None
# def id_validation(input_id):
#     try:
#         input_id = int(input_id)
#         id_split = input_id.split('-')  # 2b1d0cd5-59be-4010-83b3-b60c5e5342da
#         id = ''.join(id_split)
#     except ValueError:
#         return {"msg": f"Invalid vehicle make id #{input_id}."}
#         # os.abort(make_response(jsonify(rsp), 400))
#     return input_id


@car_bp.route('/vehicle_makes/<id>/vehicle_models', methods=['GET'])
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
# calling from frontend to get user form input as request body


@car_bp.route('/estimate', methods=['POST'])
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
    vehicle_model_id = get_vehicle_model_id(vehicle_make_id)
    
    request_body['vehicle_model_id'] = vehicle_model_id
    print(f"ready to post request {request_body}")
    response = requests.post(
        'https://www.carboninterface.com/api/v1/estimates', headers=HEADER, json=request_body)

    return response.json(), 201


@app.route('/')
def home():
    return "Welcome"

# def create_app(test_config=None):
#     app = Flask(__name__)

#     return app


# if __name__ == '__main__':
#     app.run(debug=True)
