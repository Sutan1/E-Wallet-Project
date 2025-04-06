import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from sqlalchemy import select

from extensions import db, celery_init_app
# In the following line we import all table objects that we defined in 'model_all.py' file before we call 'db.create.all' so all 
# tables will be created properly:
import model_all

from views.account import blp as Accounts_BLP
from views.user import blp as Users_BLP
from views.transaction import blp as Transactions_BLP

from model_all import TokenBlocklist

import logging
from logger import app_warning_file_handler, app_regular_file_handler
# Setting the root logger's level to INFO, so our app can capture logs while running app in docker. If running directly 
# with 'flask run' you can ommit the this line:
logging.basicConfig(level=logging.INFO)

# 'db_url=None' parameter is here in case we want to connect to external database. 
def create_app(db_url=None):
    
    app = Flask(__name__)

    app.logger.addHandler(app_warning_file_handler)
    app.logger.addHandler(app_regular_file_handler)

    # Some confige files including swagger for documentation:
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "E-Wallet App"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # In the following "os.getenv("DATABASE_URL")" used to import database connection from '.env' file in case you
    # you don't want to use default sqlite database. If nothing supplied for 'db_url=None' parameter of "def create_app" funcrion
    # and nothing is supplied for "os.getenv("DATABASE_URL")" parameter, then sqlite database "my_test_wallet_db.db" will be 
    # created by deafault:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///my_test_wallet_db.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # If you would like to run this app with flask directly without using a docker, like: 'flask run' 
    # or 'flask --app <name of this file> run', then you have to configure refis for this case. So you will have to 
    # uncomment the following line:
    # app.config["CELERY"] = {"broker_url": "redis://localhost:6379", "result_backend": "redis://localhost:6379"}

    # Alternatively use line under this comment to configure redis for docker compose. Here 'redis' is the name of service 
    # instead of 'localhost' in the previous line:
    app.config["CELERY"] = {"broker_url": "redis://redis:6379/0", "result_backend": "redis://redis:6379/0"}

    # Connecting database, celery app and Api with our app:
    db.init_app(app)
    celery_init_app(app)
    api = Api(app)
    # Creating all table objects or tables that we defined in "model_all.py" file that we already imported:
    with app.app_context():
        db.create_all()

    # Importing the secrete key for signing JWT tokens:
    app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
    jwt = JWTManager(app)
    
    # This is the function that checks each token supplied if it's in the blocklit table:
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        token = db.session.scalar(select(TokenBlocklist).where(TokenBlocklist.jti == jti))
        return token is not None
    
    # The flollowing lines that start "@jwt" decorator is just default responses for different cases:
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {"description": "Token has been revoked.", "error": "token_revoked"}
            )
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required"
                }
            )
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return(
            jsonify({"message": "The token is expired.", "error": "token expired."}),
            401.
        )
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid token."}
            ),
            401
        )
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return(
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401
        )

    # Registering blueprints that we imported:
    api.register_blueprint(Users_BLP)
    api.register_blueprint(Accounts_BLP)
    api.register_blueprint(Transactions_BLP)

    return app