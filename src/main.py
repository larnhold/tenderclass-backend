# import dependencies
import os
import sys

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
import logging

# Use src path so that the python interpreter can access all modules
sys.path.append(os.getcwd()[:os.getcwd().index('src')])

# import routes
from src.routes.v1.fetch import fetch_blueprint
from src.routes.v1.model import model_blueprint
from src.routes.v1.persistence import persistence_blueprint
from src.routes.v1.web import web_blueprint

# set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
logger.info("start tenderclass-backend")

#setup routes
app = Flask(__name__)
app.register_blueprint(model_blueprint, url_prefix="/api/v1/model")
app.register_blueprint(web_blueprint, url_prefix="/api/v1/web")
app.register_blueprint(persistence_blueprint, url_prefix="/api/v1/persistence")
app.register_blueprint(fetch_blueprint, url_prefix="/api/v1/fetch")
CORS(app)

# set up Swagger documentation
SWAGGER_URL = '/swagger'
API_URL = '/static/api.yaml'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'tenderclass-backend': "API specification for the Machine Learning classification solution for public tenders"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
