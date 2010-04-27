import datetime
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy.sql import functions
from sqlalchemy.ext.declarative import synonym_for
from repoze.bfg import security
from checking.model import meta
from checking.model.currency import Currency
from checking.model.customer import Customer


class Invoice(meta.BaseObject):
    """An invoice."""

    __tablename__ = "invoice"

    id = schema.Column(types.Integer(),
            schema.Sequence("invoice_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    _number = schema.Column("number", types.Integer())
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
        self.__acl__=[(security.Allow, account_id, ("comment", "view"))]
        if not self.sent:
            self.__acl__.append((security.Allow, account_id, ("delete", "edit")))
            if len(self.entries):
                self.__acl__.append((security.Allow, account_id, "send"))
        if self.sent and not self.paid:
            self.__acl__.append((security.Allow, account_id, "mark-paid"))

    @property
    def due(self):
        if self.sent:
            return self.sent+datetime.timedelta(days=self.payment_term)
        return None


    def total(self, type="gross"):
        assert type in ["gross", "net", "vat"]
        gross=sum([entry.total for entry in self.entries])
        if type=="gross":
            return gross

        vat=sum([v[1] for v in self.VAT()])
        if type=="vat":
            return vat
        return gross+vat


    def VAT(self):
        totals={}
        for entry in self.entries:
            current=entry.total
            totals[entry.vat]=totals.get(entry.vat, 0)+current
        for (vat, total) in totals.items():
            totals[vat]=(totals[vat]*vat)/100
        return sorted(totals.items())


    @synonym_for("_number")
    @property
    def number(self):
        if not self._number:
            return None
        return "%s.%04d" % (self.customer.invoice_code, self._number)


    def state(self):
        if not self.sent:
            return "unsend"
        elif self.paid:
            return "paid"
        today=datetime.date.today()
        due=self.sent+datetime.timedelta(days=self.payment_term)
        if due<today:
            return "overdue"
        else:
            return "pending"


    def overdue(self):
        if self.paid or not self.sent:
            return None
        today=datetime.date.today()
        due=self.sent+datetime.timedelta(days=self.payment_term)
        if due>=today:
            return None
        return (today-due).days


    def send(self):
        assert self.sent is None
        self.sent=datetime.datetime.now()
        self._number=self.customer.account.newInvoiceNumber()



class InvoiceEntry(meta.BaseObject):
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

    @property
    def total(self):
        return self.unit_price*self.units*self.currency.rate



class InvoiceNote(meta.BaseObject):
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
