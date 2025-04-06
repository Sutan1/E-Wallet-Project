from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import select
import uuid
from decimal import Decimal
from flask import current_app
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from model_all import Credit_or_Debit, Transaction_Status
from model_all import Account, Transaction
from schema import Make_Transaction_Schema, Trn_Full_Schema, Trn_In_Acc_Info_Schema

from celery_workers import make_transaction
from celery.result import AsyncResult

blp = Blueprint("blp_transactions", __name__, description = "Actions on transactions")

#_____________________________________________________
#_____________________________________________________

@blp.route("/<account_uuid>/transactions")
class All_Trns_In_Account(MethodView):
    @jwt_required(fresh=False)
    @blp.response(200, Trn_In_Acc_Info_Schema(many=True))
    def get(self,account_uuid):
        user_uuid = get_jwt_identity()
        list_of_transactions = db.session.scalar(select(Account).where(Account.account_uuid_id == account_uuid).\
                                                 where(Account.user_uuid_id == user_uuid)).transactions
        if not len(list_of_transactions.all()):
            return {"message": "You don't have any transactions yet."}
        try:
            return list_of_transactions.all()
        except Exception as e:
            db.session.rollback()
            abort (500, message = f"An Error encountered while retrieving transactions: {str(e)}")


@blp.route("/transactions/<trn_uuid>")
class Transaction_By_ID(MethodView):
    @jwt_required(fresh=False)
    @blp.response(200, Trn_Full_Schema)
    def get(self,trn_uuid):
        user_uuid = get_jwt_identity()
        transaction = db.session.scalars(select(Transaction).where(Transaction.trn_uuid_id == trn_uuid)\
                                         .where(Transaction.user_uuid_id == user_uuid)).first()
        if not transaction: 
            abort(404, message = f"Couldn't find any transaction with ID: {trn_uuid}. Please double check the transaction ID.")
        try:
            return transaction
        except Exception as e:
            db.session.rollback()
            abort(500, message = f"An error occurred while retrieving transactions: {str(e)}")


# Create Tranasction
@blp.route("/make-transaction/<account_uuid>")
class Make_Transaction(MethodView):
    @jwt_required(fresh=True)
    @blp.arguments(Make_Transaction_Schema)
    def post(self, user_data, account_uuid):
        sender_acc = db.session.scalar(select(Account).where(Account.account_uuid_id == account_uuid))
        recipient_acc = db.session.scalar(select(Account).where(Account.account_uuid_id == user_data["recipien_account_uuid"]))

        if not recipient_acc:
            abort(400, message = "Coulden't idetify recipient account!")

        elif sender_acc.balance < user_data["amount"]:
            abort(400, message = "Insufficient balance to proceed with the payment!")

        try:
            transaction_uuid = "trn:" + str(uuid.uuid4())
            sender_acc.balance -= user_data["amount"]
            outgoing_transaction = Transaction(trn_uuid_id = transaction_uuid, \
                                                direction = Credit_or_Debit("Debit"),\
                                                status = Transaction_Status("Initiated"),\
                                                amount = user_data["amount"],\
                                                counter_party_acc_name = recipient_acc.name_of_account,\
                                                counter_party_acc_uuid = user_data["recipien_account_uuid"],\
                                                counterparty_user_uuid = recipient_acc.user_uuid_id,\
                                                account_uuid_id = account_uuid,\
                                                user_uuid_id = sender_acc.user_uuid_id)
            db.session.add(outgoing_transaction)
            db.session.commit()

            result = make_transaction.delay(transaction_uuid = transaction_uuid, \
                                sender_account_uuid = account_uuid, \
                                recipient_account_uuid = user_data["recipien_account_uuid"], \
                                amount = user_data["amount"])
            return {"message":"Your payment request will be processed soon. Thank you.", "task_id": f"{result.id}"}
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning("Couldn't make a transaction in 'Transaction' route!" )
            abort(500, message = f"Couldn't initiate the payment. Error: {str(e)}")
    

@blp.route("/result/<task_id>")
class Payment_Result(MethodView):
    def get(self, task_id):
        result = AsyncResult(task_id)
        try:
            return {
                "ready": result.ready(),
                "successful": result.successful(),
                "value": result.result if result.ready() else None,
            }

        except Exception as e:
            abort(500, message = f"Somthing went wrong: {str(e)}")
        
#_____________________________________________________
#_____________________________________________________

# Testing routes

from schema import Test_All_Trns

@blp.route("/helper-all-transactions")
class All_Transactions(MethodView):
    @blp.response(200, Test_All_Trns(many=True))
    def get(self):
        return db.session.scalars(select(Transaction)).all()
    
@blp.route("/helper-all-transactions/<int:trn_id>")
class All_Transactions(MethodView):
    @blp.response(200, Trn_Full_Schema)
    def get(self, trn_id):
        return db.session.scalar(select(Transaction).where(Transaction.id == trn_id))
    
@blp.route("/helper-all-transactions/<int:trn_id>")
class Delete_Trn_By_ID(MethodView):
    def delete(self, trn_id):
        transaction = db.session.scalar(select(Transaction).where(Transaction.id == trn_id))
        if not transaction:
            abort(400, message = f"No transaction found with id: {trn_id}.")
        try:
            db.session.delete(transaction)
            db.session.commit()
            return "Transaction has been deleted."
        except Exception as e:
            abort(500, message = f"An error occurred while deleting transaction: {str(e)}")