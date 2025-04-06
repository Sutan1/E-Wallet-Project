from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import select
from decimal import Decimal
from flask import current_app
import uuid
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from extensions import db
from model_all import User, Account

from schema import Create_Account_Schema, Account_Info_Schema, Account_In_Trn_Schema
from schema import TopUp_Schema

blp = Blueprint("blp_accounts", __name__, description = "Actions on accounts")

#_____________________________________________________
#_____________________________________________________

@blp.route("/accounts")
class Create_Account(MethodView):
    @jwt_required(fresh=False)
    @blp.arguments(Create_Account_Schema)
    def post(self, user_data):
        user_uuid = get_jwt_identity()
        account_uuid = "acc:" + str(uuid.uuid4())
        account = Account(name_of_account = user_data["name_of_account"], user_uuid_id = user_uuid, \
                          account_uuid_id = account_uuid)
        try:
            db.session.add(account)
            db.session.commit()
            current_app.logger.info(f"The account has been created.\n \
                                    Details:\n \
                                    name of the account: {user_data["name_of_account"]};\n \
                                    user uuid: {user_uuid}.")
        except IntegrityError:
            abort(400, message = "Account with this name already exists!")
        except Exception as e:
            abort(500, message = f"An error occured while creating an account: {str(e)}")

        return {"message": "Account has been successfully created."}
    

    @jwt_required(fresh=False)
    @blp.response(200, Account_In_Trn_Schema(many=True))
    def get(self):
        user_uuid = get_jwt_identity()
        list_of_accounts = db.session.scalar(select(User).where(User.user_uuid_id == user_uuid)).accounts
        if not len(list_of_accounts.all()):
            return "It seems like you don't have any accounts yet."
        try:
            return list_of_accounts.all()
        except Exception as e:
            db.session.rollback()
            abort (500, message = f"An Error encountered while retrieving your accounts: {str(e)}")

        
@blp.route("/accounts/<account_uuid>")
class Account_By_ID(MethodView):
    @jwt_required(fresh=False)
    @blp.response(200, Account_Info_Schema)
    def get(self, account_uuid):
        user_uuid = get_jwt_identity()
        account = db.session.scalar(select(Account).where(Account.account_uuid_id == str(account_uuid)).\
                                    where(Account.user_uuid_id == user_uuid))
        if not account:
            abort(400, "Couldn't identify the account.")
        try:
            return account
        except Exception as e:
            db.session.rollback()
            abort(500, message = f"Somthing went wrong while finding account: {str(e)}")


@blp.route("/accounts/<account_uuid>")
class Delete_Account_By_ID(MethodView):
    @jwt_required(fresh=False)
    def delete(self, account_uuid):
        user_uuid = get_jwt_identity()
        account = db.session.scalar(select(Account).where(Account.account_uuid_id == account_uuid).\
                                    where(Account.user_uuid_id == user_uuid))        
        if not account:
            abort(400, message = "Couldn't find the account.")
        elif account.balance > Decimal(str(round(0.00, 2))):
            abort(400, message = "Account deletion is not possible at this time, as there are funds remaining in account. \
                Please ensure your account balance is zero before proceeding. \
                If you need a help please reach our costomer support team.")
        else:
            try:
                db.session.delete(account)
                db.session.commit()
                current_app.logger.info(f"The account has been deleted.\n \
                                        Details:\n \
                                        account uuid: {account.account_uuid_id};\n \
                                        account name: {account.name_of_account};\n \
                                        user uuid: {account.user_uuid_id}.")
                return {"message": "Account has been successfully deleted!"}
            except Exception as e:
                db.session.rollback() 
                abort(500, message = f"Something went wrong while deleting account: {str(e)}")

#_____________________________________________________
#_____________________________________________________

# Testing routes

@blp.route("/helper-all-accouts")
class All_Accounts(MethodView):
    @blp.response(200, Account_Info_Schema(many=True))
    def get(self):
        return db.session.scalars(select(Account)).all()

@blp.route("/helper-all-accouts/<account_uuid>")
class All_Accounts(MethodView):
    @blp.response(200, Account_Info_Schema)
    def get(self, account_uuid):
        return db.session.scalar(select(Account).where(Account.id == account_uuid))

@blp.route("/top-up/<account_uuid>")
class TopUp(MethodView):
    @blp.arguments(TopUp_Schema)
    @blp.response(200, Account_Info_Schema)
    def post(self, user_data, account_uuid):
            account = db.session.scalar(select(Account).where(Account.account_uuid_id == account_uuid))
            if not account:
                return abort(400, message = f"Couldn't identify account with this id: {account_uuid}")
            try:     
                account.balance += user_data["amount"]
                db.session.commit()
                return account
            except Exception as e:
                db.session.rollback()
            abort(500, message = f"An error occurred: {str(e)}")