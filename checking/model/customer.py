from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types
from checking.model.meta import BaseObject
from checking.model.account import Account

class Customer(BaseObject):
    """A customer
    """
    __tablename__ = "customer"

    id = schema.Column(types.Integer(),
            schema.Sequence("customer_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    account_id = schema.Column(types.Integer(),
            schema.ForeignKey(Account.id, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False)
    account = orm.relationship(Account, backref="customers")
    title = schema.Column(types.Unicode(128), nullable=False, unique=True)
    invoice_code = schema.Column(types.String(16), nullable=False, unique=True)
    ein = schema.Column(types.String(64))
    address = schema.Column(types.UnicodeText)
    postal_code = schema.Column(types.String(16))
    city = schema.Column(types.Unicode(64))
    country = schema.Column(types.String(3))
    contact_name = schema.Column(types.Unicode(64))
    contact_email = schema.Column(types.String(64))
    contact_phone = schema.Column(types.String(32))

    def __repr__(self):
        return "<Currency %s rate=%.2f>" % (self.code, self.rate)

