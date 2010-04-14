from checking.utils import SimpleTypeFactory
from checking.utils import render
from checking.model.invoice import Invoice

Factory = SimpleTypeFactory(Invoice)

def View(context, request):
    return render("invoice_view.pt", request, context,
            section="customers")

class Edit(object):
    def __init__(self, context, request):
        self.context=context
        self.request=request

    def __call__(self):
        return render("invoice_edit.pt", self.request, self.context,
                section="customers")


