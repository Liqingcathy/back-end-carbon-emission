from flask import Flask
from flask_cors import CORS

# create the object app in Flask class
def create_app(test_config=None):

    app = Flask(__name__)

    
    from .app import car_bp
    from .elastic import es_bp
    from .search import search_bp
    
    app.register_blueprint(car_bp)
    app.register_blueprint(es_bp)
    app.register_blueprint(search_bp)


    CORS(app)
    return app
