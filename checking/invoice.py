from webob.exc import HTTPFound
from validatish import validator
import formish
import schemaish
from repoze.bfg.url import route_url
from checking.utils import SimpleTypeFactory
from checking.utils import render
from checking.model import meta
from checking.model.currency import Currency
from checking.model.invoice import Invoice
from checking.model.invoice import InvoiceEntry
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



def View(context, request):
    return render("invoice_view.pt", request, context,
            section="customers")



class Edit(object):
    def __init__(self, context, request):
        self.context=context
        self.request=request
        self.form=form.CSRFForm(InvoiceSchema(), defaults=dict(
            payment_term=context.payment_term,
            entries=[entry.__dict__ for entry in context.entries]))


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


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel" or self.save():
                return HTTPFound(location=route_url("invoice_view", self.request, id=self.context.id))

        return render("invoice_edit.pt", self.request, self.context,
                status_int=202 if self.request.method=="POST" else 200,
                view=self, section="customers")


