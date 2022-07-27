import json
from flask import Flask, Blueprint, request, jsonify
import os
from dotenv import load_dotenv
import requests

load_dotenv()

car_bp = Blueprint("car_bp", __name__)

carbon_key = os.environ.get("CARBON_INTF_API_KEY")

app = Flask(__name__)

HEADER = {
        'Authorization':f'Bearer {carbon_key}',
        'Content-Type': 'application/json'
        }

#localhost:5000/vehicle_makes -> response
@car_bp.route('/vehicle_makes', methods=['GET'])
def get_vehicle_makes():
    print('backend vehicle makes request')
    '''data(list of dict): vehicle_make_id, vehicle_brand_name(limited to 4), #of models '''
    # if response.status_code != 204 and 'content-type' in response.headers and 'application/json' in response.headers['content-type']:
    response = requests.get('https://www.carboninterface.com/api/v1/vehicle_makes', headers=HEADER)
    
    return response.json(), 200

vehicle_model_id = None;
#localhost:5000/vehicle_makes/id/vehicle_models -> response
@car_bp.route('/vehicle_makes/<id>/vehicle_models', methods=['GET'])
def get_vehicle_make_id(id):
    '''data: vehicle_model_id,vehicle_model_name, vehicle_brand_name(limited to 4), year '''
    vehicle_make_id = get_vehicle_makes()['data']['id']
    response = requests.get('https://www.carboninterface.com/api/v1/vehicle_make/{vehicle_make_id}/vehicle_models', headers=HEADER)
    vehicle_model_id = response['data']['id']
    return jsonify(response.json())

#localhost:5000/estimate -> response
@car_bp.route('/estimate', methods=['POST'])
def create_estimated_val():
    response = requests.post('https://www.carboninterface.com/api/v1/estimates', headers=HEADER)
    #type, distance_unit, value, vehical_model_id incase use in database
    request_body = request.get_json()
    return jsonify(response), 201


@app.route('/')
def home():
    return "Welcome"

# def create_app(test_config=None):
#     app = Flask(__name__)

#     return app

# if __name__ == '__main__':
#     app.run(debug=True)

    