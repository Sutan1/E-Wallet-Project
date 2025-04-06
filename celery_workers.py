from flask_smorest import abort
from model_all import Account, Transaction
from model_all import Credit_or_Debit, Transaction_Status
from flask import current_app
from extensions import db
from sqlalchemy import select
from celery import shared_task

@shared_task
def make_transaction(transaction_uuid, sender_account_uuid,recipient_account_uuid, amount):
        sender_acc = db.session.scalar(select(Account).where(Account.account_uuid_id == sender_account_uuid))
        recipient_acc = db.session.scalar(select(Account).where(Account.account_uuid_id == recipient_account_uuid))
        outgooutgoing_transaction = db.session.scalar(select(Transaction).where(Transaction.trn_uuid_id == transaction_uuid).\
                                                      where(Transaction.direction == Credit_or_Debit("Debit")))
        
        if not outgooutgoing_transaction:
            current_app.logger.critical(f"Couldn't identify outgoing transaction within a worker process!\n \
                                        Details:\n \
                                        outgoung transaction uuid = {transaction_uuid},\n \
                                        sender account id = {sender_account_uuid};\n \
                                        recipient account id = {recipient_account_uuid};\n \
                                        amount = {amount}.")
            abort(500, message = f"Couldn't identify outgoing transaction within a worker process!\
                Outgoung transaction uuid: {transaction_uuid}")
                 
        
        elif not recipient_acc:
            try:
                sender_acc.balance += amount
                outgooutgoing_transaction.status = Transaction_Status("Failed")
                db.session.commit()
                current_app.logger.info(f"The payment has been reversed since worker processs couldn't identify recipent account.\n \
                                        Details:\n\
                                        outgooutgoing transaction uuid: {transaction_uuid};\n\
                                        sender_account_uuid = {sender_account_uuid};\n \
                                        recipient_account_uuid = {recipient_account_uuid};\n \
                                        amount = {amount}.")
                return {"message": f"Eventually the recipient account coulden't be idetified. \
                        So the payment has been reversed and the funds of '{amount}' amount have been returned \
                        to sender account"}
            except Exception as e:
                db.session.rollback()
                current_app.logger.critical(f"Recipient account wasn't identified within a 'worker' process and the payment hasn't been reversed.\n \
                                            Details:\n \
                                            outgooutgoing transaction uuid: {transaction_uuid};\n\
                                            sender_account_uuid = {sender_account_uuid};\n \
                                            recipient_account_uuid = {recipient_account_uuid};\n\
                                            amount = {amount};\n \
                                            Error message = f{str(e)}.")
                abort(500, message = f"Recipient account wasn't identified within a 'worker' process \
                      and the payment meant to be reversed. However, somthing went wrong.\n \
                      Error = {str(e)}")
        try:
            if sender_acc and recipient_acc and outgooutgoing_transaction:
                incoming_transaction = Transaction(trn_uuid_id = transaction_uuid,\
                                                direction = Credit_or_Debit("Credit"),\
                                                status = Transaction_Status("Processed"),\
                                                amount = amount,\
                                                counter_party_acc_name = sender_acc.name_of_account,\
                                                counter_party_acc_uuid = sender_account_uuid,\
                                                counterparty_user_uuid = sender_acc.user_uuid_id,\
                                                account_uuid_id = recipient_account_uuid,\
                                                user_uuid_id = recipient_acc.user_uuid_id)
                
                recipient_acc.balance += amount
                outgooutgoing_transaction.status = Transaction_Status("Processed")
                db.session.add(incoming_transaction)
                db.session.commit()
                current_app.logger.info(f"The paument has been successfull. Details:\n\
                                        transaction uuid: {transaction_uuid}.")
                return {"message": "The payment was successfull."}

        except Exception as e:
                sender_acc.balance += amount
                outgooutgoing_transaction.status = Transaction_Status("Failed")
                db.session.commit()
                current_app.logger.error(f"Something went wrong with the payment so it was reversed within a worker process.\n \
                                        Details:\n \
                                        outgooutgoing transaction uuid: {transaction_uuid};\n\
                                        sender_account_id = {sender_account_uuid};\n \
                                        recipient_account_id = {recipient_account_uuid};\n \
                                        amount = {amount};\n \
                                        Error message = f{str(e)}.")
                abort(500, message = f"Something went wrong with the payment so it was reversed. \
                        The funds of {amount} amount have been returned to the sender account.\n \
                        Error: {str(e)}")


# @shared_task
# def make_transaction(current_acc_id, resip_acc_id, cur_user_id,  ammount):

#     sender_account = db.session.scalar(select(Account).where(Account.id == current_acc_id))
#     recipient_account = db.session.scalar(select(Account).where(Account.id == resip_acc_id))

#     if not recipient_account:
#         abort(400, message = "Coulden't idetify recipient account! Please provide valid account.")

#     elif sender_account.balance < ammount:
#         abort(400, message = "Insufficient balance! Cannot proceed with payment.")

#     try:
#         outgoing_transaction = Transaction(direction = Credit_or_Debit("Debit"),\
#                                         amount = ammount,\
#                                             counter_party_name = recipient_account.name_of_account,\
#                                                 counter_party_acc_id = resip_acc_id,\
#                                                     account_id = current_acc_id,\
#                                                         user_id = cur_user_id)

#         incoming_transaction = Transaction(direction = Credit_or_Debit("Credit"),\
#                                         amount = ammount,\
#                                             counter_party_name = sender_account.name_of_account,\
#                                                 counter_party_acc_id = current_acc_id,\
#                                                     account_id = resip_acc_id,\
#                                                         user_id = recipient_account.user_id)

        
#         sender_account.balance -= round(ammount, 2)
#         recipient_account.balance += round(ammount, 2)
#         db.session.add(outgoing_transaction)
#         db.session.add(incoming_transaction)
#         db.session.commit()
#         return {"message": "The payment was successfull."}

#     except Exception as e:
#         db.session.rollback()
#         abort(500, message = f"An error occurred while making transactions: {str(e)}")