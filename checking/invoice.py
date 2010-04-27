import datetime
from webob.exc import HTTPFound
from validatish import validator
import formish
import schemaish
from sqlalchemy import sql
from sqlalchemy import func
from repoze.bfg.exceptions import Forbidden
from repoze.bfg.url import route_url
from checking.authentication import currentUser
from checking.utils import SimpleTypeFactory
from checking.utils import render
from checking.utils import checkCSRF
from checking.model import meta
from checking.model.currency import Currency
from checking.model.customer import Customer
from checking.model.invoice import Invoice
from checking.model.invoice import InvoiceEntry
from checking.model.invoice import InvoiceNote
from checking import form

Factory = SimpleTypeFactory(Invoice)


class InvoiceEntrySchema(schemaish.Structure):
    id = schemaish.Integer()
    description = schemaish.String(validator=validator.Required())
    currency_code = schemaish.String(validator=validator.Required())
    vat = schemaish.Integer(validator=validator.Required())
    unit_price = schemaish.Decimal(validator=validator.Required())
    units = schemaish.Decimal(validator=validator.All(
        validator.Required(),
        validator.Range(min=1)))


class InvoiceSchema(schemaish.Structure):
    payment_term = schemaish.Integer(validator=validator.All(
        validator.Required(),
        validator.Range(min=1)))
    entries = schemaish.Sequence(attr=InvoiceEntrySchema())


class PaidSchema(schemaish.Structure):
    paid = schemaish.Date(validator=validator.Required())


class NoteSchema(schemaish.Structure):
    comment = schemaish.String(validator=validator.Required())


def Overview(request):
    user=currentUser(request)
    session=meta.Session()

    query=sql.select([Invoice.id, Customer.invoice_code, Invoice.number, Invoice.sent, Invoice.payment_term, Invoice.paid,
                      sql.select([func.sum(InvoiceEntry.units*InvoiceEntry.unit_price*Currency.rate)],
                                 InvoiceEntry.invoice_id==Invoice.id).as_scalar().label("amount")],
                      Customer.account_id==user.id,
                      sql.join(Invoice.__table__, Customer.__table__, Invoice.customer_id==Customer.id))\
            .group_by(Invoice.id, Customer.invoice_code, Invoice.number, Invoice.sent, Invoice.payment_term, Invoice.paid)\
            .order_by(Invoice.sent.desc())\
            .limit(10)

    today=datetime.date.today()
    def morph(row):
        due=(row.sent+datetime.timedelta(days=row.payment_term)) if row.sent else None
        if not row.sent:
            state="unsend"
        elif row.paid:
            state="paid"
        elif due<today:
            state="overdue"
        else:
            state="pending"
        return dict(id=row.id,
                   number="%s.%04d" % (row.invoice_code, row.number) if row.number else None,
                   sent=row.sent,
                   due=(row.sent+datetime.timedelta(days=row.payment_term)) if row.sent else None,
                   paid=row.paid,
                   amount=row.amount or 0,
                   state=state,
                   overdue=(today-due).days if row.sent and not row.paid and due<today else None,
                   url=route_url("invoice_view", request, id=row.id))


    invoices=[morph(row) for row in session.execute(query)]

    return render("invoice_overview.pt", request,
            section="invoices",
            invoices=invoices)



def View(context, request):
    subtotal=context.total
    vats={}
    for entry in context.entries:
        if not entry.vat:
            continue
        vats[entry.vat]=vats.get(entry.vat, 0)+entry.total
    if vats:
        vat_totals=sorted([(vat, amount*vat/100) for (vat,amount) in vats.items()])
        grandtotal=subtotal+sum([vat[1] for vat in vat_totals])
    else:
        vat_totals=[]
        grandtotal=subtotal
        subtotal=None
    vats=sorted(vats.items())

    return render("invoice_view.pt", request, context,
            section="customers",
            subtotal=subtotal,
            vat_totals=vat_totals,
            grandtotal=grandtotal)



class Edit(object):
    def __init__(self, context, request):
        self.context=context
        self.customer=context.customer
        self.request=request
        self.form=form.CSRFForm(InvoiceSchema(), defaults=dict(
            payment_term=context.payment_term,
            entries=[entry.__dict__ for entry in context.entries]))


    @property
    def action(self):
        return route_url("invoice_edit", self.request,
                id=self.context.id)


    def save(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        session=meta.Session()
        currencies=dict(session.query(Currency.code, Currency.id)\
                .filter(Currency.until==None).all())

        self.context.payment_term=data["payment_term"]

        current=dict([(entry.id, entry) for entry in self.context.entries])
        for (position,entry) in enumerate(data["entries"]):
            if entry["id"]:
                c=current.get(entry["id"])
                if c is None:
                    continue
                del current[c.id]
            else:
                c=InvoiceEntry(invoice=self.context)
                session.add(c)

            c.position=position
            c.currency_id=currencies[entry["currency_code"]]
            c.unit_price=entry["unit_price"]
            c.units=entry["units"]
            c.description=entry["description"]
            c.vat=entry["vat"]

        for entry in current.values():
            session.remove(entry)

        return True


    def cancel(self):
        return HTTPFound(location=route_url("invoice_view", self.request, id=self.context.id))


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel" or self.save():
                return self.cancel()

        return render("invoice_edit.pt", self.request, self.context,
                status_int=202 if self.request.method=="POST" else 200,
                view=self, section="customers")


class Add(Edit):
    def __init__(self, context, request):
        self.context=None
        self.customer=context
        self.request=request
        self.form=form.CSRFForm(InvoiceSchema())

    @property
    def action(self):
        return route_url("customer_add_invoice", self.request,
                id=self.customer.id)

    def save(self):
        self.context=Invoice(customer=self.customer)
        if Edit.save(self):
            meta.Session.add(self.context)
            return True
        return False

    def cancel(self):
        return HTTPFound(location=route_url("customer_view", self.request, id=self.customer.id))



def Delete(context, request):
    if request.method=="POST":
        if not checkCSRF(request):
            raise Forbidden("Invalid CSRF token")
        if request.POST.get("action", "cancel")=="confirm":
            meta.Session.delete(context)
            return HTTPFound(location=route_url("customer_view", request, id=context.customer_id))
        return HTTPFound(location=route_url("invoice_view", request, id=context.id))

    return render("invoice_delete.pt", request, context,
            status_int=202 if request.method=="POST" else 200,
            section="customers",
            action_url=route_url("invoice_delete", request, id=context.id))


def AjaxDelete(context, request):
    if request.method=="POST":
        if not checkCSRF(request):
            raise Forbidden("Invalid CSRF token")
        if request.POST.get("action", "cancel")=="confirm":
            meta.Session.delete(context)
            return dict(action="redirect",
                        location=route_url("customer_view", request, id=context.customer_id))
        return dict(action="close")

    return render("invoice_delete.pt", request, context,
            status_int=202 if request.method=="POST" else 200,
            section="customers",
            action_url=route_url("invoice_delete", request, id=context.id))


def Send(context, request):
    if request.method=="POST":
        if not checkCSRF(request):
            raise Forbidden("Invalid CSRF token")
        if request.POST.get("action", "cancel")=="confirm":
            context.send()
        return HTTPFound(location=route_url("invoice_view", request, id=context.id))

    return render("invoice_send.pt", request, context,
            status_int=202 if request.method=="POST" else 200,
            section="customers",
            action_url=route_url("invoice_send", request, id=context.id))


def AjaxSend(context, request):
    if request.method=="POST":
        if not checkCSRF(request):
            raise Forbidden("Invalid CSRF token")

        if request.POST.get("action", "cancel")=="confirm":
            context.send()
            return dict(action="reload")

        return dict(action="close")

    return render("invoice_send.pt", request, context,
            status_int=202 if request.method=="POST" else 200,
            section="customers",
            action_url=route_url("invoice_send", request, id=context.id))


class Paid(object):
    def __init__(self, context, request):
        self.context=context
        self.request=request
        self.form=form.CSRFForm(PaidSchema(),
            defaults=dict(paid=datetime.date.today()))
        self.form["paid"].widget=formish.DateParts()


    def save(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        self.context.paid=data["paid"]
        return True


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel" or self.save():
                return HTTPFound(location=route_url("invoice_view", self.request, id=self.context.id))

        return render("invoice_paid.pt", self.request, self.context,
                status_int=202 if self.request.method=="POST" else 200,
                section="customers", view=self,
                action_url=route_url("invoice_paid", self.request, id=self.context.id))


class AjaxPaid(Paid):
    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel":
                return dict(action="close")
            if self.save():
                return dict(action="reload")

        return render("invoice_paid.pt", self.request, self.context,
                status_int=202 if self.request.method=="POST" else 200,
                section="customers", view=self,
                action_url=route_url("invoice_paid", self.request, id=self.context.id))



def Comment(context, request):
    if request.method=="POST":
        try:
            data=form.CSRFForm(NoteSchema()).validate(request)
        except formish.FormError:
            return HTTPFound(location=route_url("invoice_view", request, id=context.id))

        context.notes.append(InvoiceNote(comment=data["comment"]))

    return HTTPFound(location=route_url("invoice_view", request, id=context.id))

