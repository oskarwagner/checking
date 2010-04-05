from webob.exc import HTTPFound
import formish
from repoze.bfg.url import route_url
from checking import form
from checking.utils import render
from checking.utils import SimpleTypeFactory
from checking.authentication import currentUser
from checking.model.customer import Customer
from checking.model import meta


CustomerSchema = form.OrmToSchema(Customer, exclude=["id", "account_id"])
Factory = SimpleTypeFactory(Customer)

def Overview(request):
    user=currentUser(request)

    return render("customer_overview.pt", request,
            section="customers",
            customers=[])


class Add(object):
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


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel" or self.save():
                return HTTPFound(location=route_url("customer_view", self.request, id=self.context.id))
        
        return render("customer_edit.pt", self.request, self.context,
                status_int=202 if self.request.method=="POST" else 200,
                view=self, section="customers",
                action_url=route_url("customer_edit", self.request, id=self.context.id))
                


def View(context, request):
    return render("customer_view.pt", request, context,
            section="customers",
            edit_url=route_url("customer_edit", request, id=context.id))

