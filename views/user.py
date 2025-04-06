from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy import select
from datetime import timedelta
from decimal import Decimal
import uuid
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt

from extensions import db
from model_all import TokenBlocklist
from schema import Token_All_Schema
from model_all import User
from schema import User_Plain_Schema

blp = Blueprint("blp_users", __name__, description = "Actions on users")

#_____________________________________________________
#_____________________________________________________

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(User_Plain_Schema)
    def post(self, user_data):
        if db.session.scalar(select(User).where(User.user_name == user_data["user_name"])):
            abort(409, message = "A user with this name already exists.")

        try:
            uuid_id = "user:" + str(uuid.uuid4())
            user = User(user_name = user_data["user_name"], password = pbkdf2_sha256.hash(user_data["password"]), \
                        user_uuid_id = uuid_id)
            
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"A user has been registered, name: {str(user_data["user_name"])}")

        except Exception as e:
            db.session.rollback()
            abort (500, message = f"An error occurred while creating the user: {str(e)}")

        return {"message": f"Dear {user.user_name}, you are successfully registerd."}
    

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(User_Plain_Schema)
    def post(self, user_data):
        user = db.session.scalar(select(User).where(User.user_name == user_data["user_name"]))

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=str(user.user_uuid_id), fresh=True, expires_delta=timedelta(minutes=5))
            refresh_token = create_refresh_token(identity=str(user.user_uuid_id), expires_delta=timedelta(hours=1))
            return {"message": f"Dear{user.user_name}, you are logged in.", "access_token": access_token,\
                    "refresh_token": refresh_token}

        abort(401, message="Invalid credentials.")

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def get(self):
        curent_user_uuid = get_jwt_identity()
        jti = get_jwt()["jti"]
        try:
            db.session.add(TokenBlocklist(jti = jti))
            db.session.commit()
            access_token = create_access_token(identity=curent_user_uuid, fresh=False, expires_delta=timedelta(hours=1))
        except Exception as e:
            db.session.rollback()
            abort (500, message = "Somthing went wrong while saving old token.")

        return {"non_fresh_access_token": access_token}
    
@blp.route("/logout")
class Logout(MethodView):
    @jwt_required(refresh=False)
    def get(self):
        jti = get_jwt()["jti"]
        try:
            db.session.add(TokenBlocklist(jti = jti))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort (500, message = "Somthing went wrong while saving an old token.")

        return {"You are logged out!"}

@blp.route("/delete-user")
class Delete_User(MethodView):
    @jwt_required(fresh=False)
    def delete(self):
        curent_user_uuid = get_jwt_identity()
        user = db.session.scalar(select(User).where(User.user_uuid_id == curent_user_uuid))
        user_name = user.user_name

        if not user:
            abort(400, message = "Couldn't identify user!")

        elif user:
            for account in user.accounts:
                if account.balance > Decimal(0):
                    abort(400, message = "Cannot delete user while it has associated account(s) with positive balance!")

        try:
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info(f"User has deleted the account.Deatail:\n \
                                    name: {user_name};\n \
                                    id: {curent_user_uuid}.")
            return {"message": f"User: {user_name} has been successfully deleted."}
        except Exception as e:
            abort(500, message = "Somthing went wrong while deleting the user. Please try again.")


# Testing routes
@blp.route("/helper-users")
class Helper_All_Users(MethodView):
    @blp.response(200, User_Plain_Schema(many=True))
    def get(self):
        return db.session.scalars(select(User)).all()
    
@blp.route("/helper-users/<user_uuid>")
class Helper_Each_Users(MethodView):
    def get(self,user_uuid):
        return db.session.scalar(select(User).where(User.user_uuid_id == user_uuid))
 
@blp.route("/helper-users/<user_uuid>")
class Helper_Delete_Users(MethodView):
    def delete(self,user_uuid):
        user = db.session.scalar(select(User).where(User.user_uuid_id == user_uuid))
        
        if not user:
            abort(400, message = f"Couldn't identify user with id: {user_uuid}.")

        try:
            db.session.delete(user)
            db.session.commit()
            return "User has been successfully deleted."
        except Exception as e:
            db.session.rollback()
            abort(500, message = f"Somthing went wrong while finding account: {str(e)}")

#_____________________________________________________
#_____________________________________________________

# See all tokens in DB:

@blp.route("/tokens")
class All_Token(MethodView):
    @blp.response(200, Token_All_Schema(many=True))
    def get(self):
        return db.session.scalars(select(TokenBlocklist)).all()