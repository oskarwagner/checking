from validatish import validator
import schemaish
from checking.utils import SimpleTypeFactory
from checking.utils import render
from checking.model.invoice import Invoice
from checking.model.invoice import InvoiceEntry
from checking import form

Factory = SimpleTypeFactory(Invoice)
InvoiceEntrySchema = form.OrmToSchema(InvoiceEntry,
        exclude=["position", "invoice_id" ])

class InvoiceSchema(schemaish.Structure):
    payment_term = schemaish.Integer(validator=validator.All(
        validator.Required(),
        validator.Range(min=1)))
    entries = schemaish.Sequence(attr=InvoiceEntrySchema)



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


    def __call__(self):
        return render("invoice_edit.pt", self.request, self.context,
                view=self,
                section="customers")


