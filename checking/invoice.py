from checking.utils import SimpleTypeFactory
from checking.utils import render
from checking.model.invoice import Invoice

Factory = SimpleTypeFactory(Invoice)

def View(context, request):
    return render("invoice_view.pt", request, context,
            section="customers")
