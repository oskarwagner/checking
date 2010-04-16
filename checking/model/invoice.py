import datetime
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy.sql import functions
from repoze.bfg import security
from checking.model.meta import BaseObject
from checking.model.currency import Currency
from checking.model.customer import Customer


class Invoice(BaseObject):
    """An invoice."""

    __tablename__ = "invoice"

    id = schema.Column(types.Integer(),
            schema.Sequence("invoice_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    number = schema.Column(types.Integer())
    customer_id = schema.Column(types.Integer(),
            schema.ForeignKey(Customer.id, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False)
    customer = orm.relationship(Customer, backref="invoices")
    sent = schema.Column(types.Date())
    payment_term = schema.Column(types.Integer(), nullable=False, default=30)
    paid = schema.Column(types.Date())
    note = schema.Column(types.UnicodeText())

    @orm.reconstructor
    def _add_acls(self):
        account_id=self.customer.account_id
        self.__acl__=[(security.Allow, account_id, "view")]
        if not self.sent:
            self.__acl__.append((security.Allow, account_id, "edit"))

    @property
    def due(self):
        if self.sent:
            return self.sent+datetime.timedelta(days=self.payment_term)
        return None



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
    vat = schema.Column(types.Integer(), nullable=False)
    currency_id = schema.Column(types.Integer(3),
            schema.ForeignKey(Currency.id, onupdate="RESTRICT", ondelete="RESTRICT"),
            nullable=False)
    currency = orm.relationship(Currency, lazy="joined")
    unit_price = schema.Column(types.Numeric(precision=6, scale=2), nullable=False)
    units = schema.Column(types.Numeric(4,2), nullable=False, default=1)



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
