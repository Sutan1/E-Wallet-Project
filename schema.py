from marshmallow import Schema, fields
from decimal import Decimal

# Custom Float field for only 2 decimal values, like '0.00'
class TwoDecimalFloat(fields.Float):
    # def _serialize(self, value, attr, obj, **kwargs):
    #     if value is not None:
    #         value = round(value, 2)
    #     return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # Call the parent class's _deserialize method to handle basic validation
        value = super()._deserialize(value, attr, data, **kwargs)
        # Round the value to 2 decimal places after deserialization
        return Decimal(str(round(value, 2)))
    
#________________________________________________
#________________________________________________

class User_Plain_Schema(Schema):
    id = fields.Int()
    user_uuid_id = fields.Str(dump_only=True)
    user_name = fields.Str(required=False)
    password = fields.Str(required=False, load_only=True)

class Create_Account_Schema(Schema):
    name_of_account = fields.Str(required = True, load_only=True)        

class Trn_In_Acc_Info_Schema(Schema):
    id = fields.Int(dump_only = True)
    trn_uuid_id = fields.Str(dump_only = True)
    direction = fields.Str(dump_only = True)
    amount = TwoDecimalFloat(dump_only = True)
    # created_datetime = fields.DateTime(dump_only = True)
    # counter_party_name = fields.Str(dump_only = True)
    # counter_party_acc_id = fields.Int(dump_only = True)
    # user_account_id = fields.Int(dump_only = True)
    # account_id = fields.Int(dump_only = True)

class Account_In_Trn_Schema(Schema):
    id = fields.Int(dump_only = True)
    account_uuid_id = fields.Str(dump_only = True)
    name_of_account = fields.Str(dump_only = True)
    # balance = TwoDecimalFloat(dump_only = True)
    # user_id = fields.Int(dump_only = True)
    # transactions = fields.List(fields.Nested(Trn_In_Acc_Info_Schema()), dump_only = True)

class Account_Info_Schema(Account_In_Trn_Schema):

    id = fields.Int(dump_only = True)
    name_of_account = fields.Str(dump_only = True)
    balance = TwoDecimalFloat(dump_only = True)
    user_id = fields.Int(dump_only = True)
    # transactions = fields.List(fields.Nested(Trn_In_Acc_Info_Schema()), dump_only = True)

#________________________________________________
#________________________________________________

class Trn_Full_Schema(Trn_In_Acc_Info_Schema):
    # id = fields.Int(dump_only = True)
    # direction = fields.Str(dump_only = True)
    # amount = TwoDecimalFloat(dump_only = True)
    created_datetime = fields.DateTime(dump_only = True)
    counter_party_acc_name = fields.Str(dump_only = True)
    counter_party_acc_uuid = fields.Str(dump_only = True)
    # user_id = fields.Int(dump_only = True)
    account_id = fields.Int(dump_only = True)
    account = fields.Nested(Account_In_Trn_Schema(), dump_only = True)

#________________________________________________
#________________________________________________

class Make_Transaction_Schema(Schema):
    recipien_account_uuid = fields.Str(required=True, load_only=True)
    amount = TwoDecimalFloat(required=True, load_only=True)

#________________________________________________
#________________________________________________
# Testing Schemas for top up or substract balance

class TopUp_Schema(Schema):
    amount = TwoDecimalFloat(required=True)

#_____________

class Acc_Name_Schema(Schema):
     name_of_account = fields.Str(dump_only = True)

class Test_All_Trns(Schema):
    # id = fields.Int(dump_only = True)
    trn_uuid_id = fields.Str(dump_only = True)
    direction = fields.Str(dump_only = True)
    status = fields.Str(dump_only = True)
    amount = TwoDecimalFloat(dump_only = True)
    account = fields.Nested(Acc_Name_Schema(), dump_only = True)
    counter_party_acc_name = fields.Str(dump_only = True)

#________________________________________________
#________________________________________________

class Token_All_Schema(Schema):
    id = fields.Int(dump_only = True)
    jti = fields.Str(dump_only = True)
    created_datetime = fields.DateTime(dump_only = True)