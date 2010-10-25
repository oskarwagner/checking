import datetime
from webob.exc import HTTPFound
from validatish import validator
import formish
import schemaish
from sqlalchemy import orm
from repoze.bfg.exceptions import Forbidden
from repoze.bfg.view import bfg_view
from repoze.bfg.url import route_url
from checking.authentication import currentUser
from checking.utils import SimpleTypeFactory
from checking.utils import checkCSRF
from checking.utils import render
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


def summaryInvoices(invoices):
    def morph(invoice):
        info=dict(id=invoice.id,
                  number=invoice.number,
                  total_gross=invoice.total("gross"),
                  total_vat=invoice.total("vat"),
                  state=invoice.state(),
                  sent=invoice.sent,
                  paid=invoice.paid,
                  overdue=invoice.overdue())
        info["total_net"]=info["total_gross"]+info["total_vat"]
        return info

    invoices=[morph(invoice) for invoice in invoices]

    return dict(invoices=invoices,
                total_gross=sum([i["total_gross"] for i in invoices]),
                total_vat=sum([i["total_vat"] for i in invoices]),
                total_net=sum([i["total_net"] for i in invoices]))


def Overview(request):
    user=currentUser(request)
    session=meta.Session()

    invoices=session.query(Invoice)\
            .select_from(orm.join(Invoice, Customer))\
            .filter(Customer.account==user)\
            .order_by(Invoice.sent.desc())\
            .options(orm.joinedload(Invoice.entries))

    summary=summaryInvoices(invoices)

    return render("invoice_overview.pt", request,
            section="invoices",
            **summary)



def View(context, request):
    return render("invoice_view.pt", request, context, section="customers")



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



@bfg_view(route_name="invoice_print", permission="view")
def Print(context, request):
    from z3c.rml.document import Document
    from repoze.bfg.renderers import render
    from lxml import etree
    from cStringIO import StringIO
    from webob import Response

    rml=render("checking:rml/invoice.rml.pt", {}, request)
    doc=Document(etree.fromstring(rml))
    output=StringIO()
    doc.process(output)
    output.seek(0)
    response=Response(output.read())
    response.content_type="application/pdf"
    response.headers.add("Content-Disposition", "attachment; filename=%s.pdf" % context.number)
    return response


