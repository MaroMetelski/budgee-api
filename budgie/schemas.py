from marshmallow import Schema, fields, validate


ACCOUNT_TYPES = ("expense", "income", "equity", "asset", "liability")


class UserSchema(Schema):
    id = fields.UUID()
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)
    salt = fields.Str(required=True)
    created = fields.Date(required=True)


class AccountSchema(Schema):
    class Meta:
        ordered = True

    id = fields.UUID()
    name = fields.Str(required=True)
    type = fields.Str(required=True, validate=validate.OneOf(ACCOUNT_TYPES))
    description = fields.Str(load_default="", dump_default="")


class EntrySchema(Schema):
    class Meta:
        ordered = True

    id = fields.UUID()
    when = fields.Date(required=True)
    credit_account = fields.Str(required=True)
    debit_account = fields.Str(required=True)
    amount = fields.Decimal(places=2, required=True, as_string=True)
    who = fields.Str(load_default="", dump_default="")
    description = fields.Str(load_default="", dump_default="")
    tags = fields.List(fields.Str)
