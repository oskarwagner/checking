from checking.form import OrmToSchema
from checking.utils import render
from checking.authentication import currentUser
from checking.model.customer import Customer


CustomerSchema = OrmToSchema(Customer, exclude=["id", "account_id"])

def Overview(request):
    user=currentUser(request)

    return render("customer_overview.pt", request,
            customers=[])


class Add(object):
    def __init__(self, context, request):
        self.context=context
        self.request=request

