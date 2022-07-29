from flask import Flask
from elasticsearch import Elasticsearch
from flask_cors import CORS

#create the object app in Flask class
def create_app(test_config=None):
    
    app = Flask(__name__)
    from .app import car_bp
    app.register_blueprint(car_bp)
    CORS(app)
    return app



