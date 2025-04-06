from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, DateTime, String, Integer, ForeignKey, Enum, Numeric, UniqueConstraint
from typing import List
import enum
from extensions import db

class Transaction_Status(enum.Enum):
    Initiated = "Initiated"
    Processed = "Processed"
    Failed = "Failed"

class Credit_or_Debit(enum.Enum):
    Credit = "Credit"
    Debit = "Debit"


class User(db.Model):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True)
    user_uuid_id = mapped_column(String, nullable=False, unique=True)
    user_name = mapped_column(String(255), nullable=False, unique=True)
    password = mapped_column(String(255), nullable=False)
    created_date = mapped_column(DateTime, nullable=False, default=func.now())

    # Relationships
    accounts: Mapped[List["Account"]] = relationship(back_populates="user", lazy="dynamic")

    # accounts: Mapped[List["Account"]] = relationship(back_populates="user_main", lazy="dynamic",\
    #                                                          order_by="Account.created_datetime")

#_____________________________________________________
#_____________________________________________________

    # Internal Accounts

class Account(db.Model):
    __tablename__ = "internal_account"
    # __table_args__ = (db.UniqueConstraint('name_of_account', 'user_id'),)

    id = mapped_column(Integer, primary_key=True)
    account_uuid_id = mapped_column(String, nullable=False, unique=True)
    name_of_account = mapped_column(String, nullable=False)
    balance = mapped_column(Numeric(10,2), nullable=False, default = 0.00)
    created_datetime = mapped_column(DateTime, nullable=False, default=func.now())
    

    # Relationships with User
    user_uuid_id = mapped_column(ForeignKey("users.user_uuid_id"), nullable=True)
    user: Mapped["User"] = relationship(back_populates = "accounts", lazy="joined")

    # Relationships with Transaction
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account",\
                                                                    lazy="dynamic")
    
    __table_args__ = (UniqueConstraint('user_uuid_id', 'name_of_account', name='_uix_user_uuid_acc_name'),)
#_____________________________________________________
#_____________________________________________________

    # Transactions

class Transaction(db.Model):
    __tablename__ = "transaction"

    id = mapped_column(Integer, primary_key=True)
    trn_uuid_id = mapped_column(String, nullable=False)
    direction = mapped_column(Enum(Credit_or_Debit), nullable=False)
    status = mapped_column(Enum(Transaction_Status), nullable=False)
    amount = mapped_column(Numeric(10,2), nullable=False)
    created_datetime = mapped_column(DateTime, nullable=False, default=func.now())
    
    counter_party_acc_name = mapped_column(String, nullable=False)
    counter_party_acc_uuid = mapped_column(Integer, nullable=False)
    counterparty_user_uuid = mapped_column(Integer, nullable=False)

# Relationships with Internal Accounts
    user_uuid_id = mapped_column(Integer, nullable=True)
    account_uuid_id = mapped_column(ForeignKey("internal_account.account_uuid_id"), nullable=True)
    account: Mapped["Account"] = relationship("Account", back_populates="transactions",\
                                                                  lazy="joined")
    
    __table_args__ = (UniqueConstraint('trn_uuid_id', 'direction', name='_uix_trn_uuid_direction'),)
    
#_____________________________________________________
#_____________________________________________________

    # Tokens

class TokenBlocklist(db.Model):
    __tablename__ = "revoked_jwt_tokens"

    id = mapped_column(Integer, primary_key=True)
    jti = mapped_column(String(50), nullable=False, index=True)
    created_datetime = mapped_column(DateTime, nullable=False, default=func.now())

#_____________________________________________________
#_____________________________________________________

# class Transaction_Status(db.Model):
#     __tablename__ = "transaction_status"

#     id = mapped_column(Integer, primary_key=True)
#     status = mapped_column(Enum(Transaction_Status), nullable=False)
#     amount = mapped_column(Numeric(10,2), nullable=False)
#     created_datetime = mapped_column(DateTime, nullable=False, default=func.now())
#     celery_worker_id = mapped_column(String, nullable=False, index=True)
    
#     sender_acc_id = mapped_column(Integer, nullable=False)
#     sender_acc_name = mapped_column(String, nullable=False)
#     sender_user_id = mapped_column(Integer, nullable=False)

#     recipient_acc_id = mapped_column(Integer, nullable=False)
#     recipient_acc_name = mapped_column(String, nullable=False)
#     recipient_user_id = mapped_column(Integer, nullable=False)