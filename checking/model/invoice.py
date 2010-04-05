from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy.sql import functions
from checking.model.meta import BaseObject
from checking.model.account import Account
from checking.model.currency import Currency
from checking.model.customer import Customer

class Invoice(BaseObject):
    """An invoice."""

    __tablename__ = "invoice"

    id = schema.Column(types.Integer(),
            schema.Sequence("invoice_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    account_id = schema.Column(types.Integer(),
            schema.ForeignKey(Account.id, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False)
    account = orm.relationship(Account, backref="customers")
    number = schema.Column(types.Integer())
    customer_id = schema.Column(types.Integer(),
            schema.ForeignKey(Customer.id, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False)
    customer = orm.relationship(Customer)
    sent = schema.Column(types.DateTime())
    paid = schema.Column(types.DateTime())
    note = schema.Column(types.UnicodeText())


class InvoiceEntry(BaseObject):
    __tablename__ = "invoice_entry"

    id = schema.Column(types.Integer(),
            schema.Sequence("invoice_entry_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    position = schema.Column(types.Integer(), default=0)
    invoice_id = schema.Column(types.Integer(),
            schema.ForeignKey(Invoice.id, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False)
    invoice = orm.relationship(Invoice,
            backref=orm.backref("entries", order_by=position))
    description = schema.Column(types.UnicodeText(), nullable=False)
    currency_code = schema.Column(types.String(3),
            schema.ForeignKey(Currency.code, onupdate="RESTRICT", ondelete="RESTRICT"),
            nullable=False)
    amount = schema.Column(types.Numeric(precision=6, scale=2), nullable=False)
    standardised_amount = schema.Column(types.Numeric(precision=6, scale=2),
            nullable=False)


class InvoiceNote(BaseObject):
    __tablename__ = "invoice_note"

    id = schema.Column(types.Integer(),
            schema.Sequence("invoice_note_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    posted = schema.Column(types.DateTime(), nullable=False,
            default=functions.now())
    invoice_id = schema.Column(types.Integer(),
            schema.ForeignKey(Invoice.id, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False)
    invoice = orm.relationship(Invoice,
            backref=orm.backref("notes", order_by=posted))
    comment = schema.Column(types.UnicodeText(), nullable=False)
