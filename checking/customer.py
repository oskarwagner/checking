import datetime
from webob.exc import HTTPFound
import formish
from sqlalchemy import sql
from sqlalchemy import func
from repoze.bfg.url import route_url
from checking import form
from checking.utils import render
from checking.utils import SimpleTypeFactory
from checking.authentication import currentUser
from checking.model.currency import Currency
from checking.model.customer import Customer
from checking.model.invoice import Invoice
from checking.model.invoice import InvoiceEntry
from checking.model import meta


CustomerSchema = form.OrmToSchema(Customer, exclude=["id", "account_id"])
Factory = SimpleTypeFactory(Customer)

def Overview(request):
    user=currentUser(request)
    session=meta.Session()
    customers=session.query(Customer.id, Customer.title, Customer.invoice_code)\
            .filter(Customer.account==user)\
            .order_by(Customer.title)
    customers=[dict(id=row.id,
                    title=row.title,
                    invoice_code=row.invoice_code,
                    url=route_url("customer_view", request, id=row.id))
               for row in customers]
    return render("customer_overview.pt", request,
            section="customers",
            customers=customers)


class Add(object):
    can_modify_invoice_code = True

    def __init__(self, context, request):
        self.context=context
        self.request=request
        self.form=form.CSRFForm(CustomerSchema)

    def save(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        user=currentUser(self.request)
        customer=Customer(account=user, **data)
        meta.Session.add(customer)
        return True


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel" or self.save():
                return HTTPFound(location=route_url("customers", self.request))
        
        return render("customer_edit.pt", self.request, 
                status_int=202 if self.request.method=="POST" else 200,
                view=self, section="customers",
                action_url=route_url("customer_add", self.request))
                


class Edit(object):
    can_modify_invoice_code = False

    def __init__(self, context, request):
        self.context=context
        self.request=request
        self.form=form.CSRFForm(CustomerSchema, defaults=context.__dict__)

    def save(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        for (key,value) in data.items():
            setattr(self.context, key, value)

        return True


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel" or self.save():
                return HTTPFound(location=route_url("customer_view", self.request, id=self.context.id))
        
        return render("customer_edit.pt", self.request, self.context,
                status_int=202 if self.request.method=="POST" else 200,
                view=self, section="customers",
                action_url=route_url("customer_edit", self.request, id=self.context.id))
                


def View(context, request):
    session=meta.Session()
    query=sql.select([Invoice.id, Invoice.number, Invoice.sent, Invoice.payment_term, Invoice.paid,
                      sql.select([func.sum(InvoiceEntry.units*InvoiceEntry.unit_price*Currency.rate)],
                                 InvoiceEntry.invoice_id==Invoice.id).as_scalar().label("amount")],
                      Invoice.customer_id==context.id)\
            .group_by(Invoice.id, Invoice.number, Invoice.sent, Invoice.payment_term, Invoice.paid)\
            .order_by(Invoice.sent.desc())\
            .limit(10)

    invoices=[dict(id=row.id,
                   number="%s.%04d" % (context.invoice_code, row.number) if row.number else None,
                   sent=row.sent,
                   due=(row.sent+datetime.timedelta(days=row.payment_term)) if row.sent else None,
                   paid=row.paid,
                   amount=row.amount or 0,
                   url=route_url("invoice_view", request, id=row.id))
               for row in session.execute(query)]

    return render("customer_view.pt", request, context,
            section="customers",
            invoices=invoices,
            edit_url=route_url("customer_edit", request, id=context.id))



