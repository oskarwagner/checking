from webob.exc import HTTPFound
import formish
import schemaish
from validatish import validator
from repoze.bfg.url import route_url
from checking import form
from checking.authentication import loginUser
from checking.model import meta
from checking.model.account import Account
from checking.utils import render

class SignupSchema(schemaish.Structure):
    login = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(min=5, max=32),
        validator.PlainText(),
        form.AvailableLogin()))
    password = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(min=5, max=255)))
    email = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(max=255),
        validator.Email()))
    firstname = schemaish.String(validator=validator.Length(max=255))
    surname = schemaish.String(validator=validator.Length(max=255))
    terms = schemaish.Boolean(validator=form.MustAgree())


class Signup(object):
    def __init__(self, request):
        self.request=request
        self.form=form.Form(SignupSchema())
        self.form["password"].widget=formish.CheckedPassword()
        self.form["terms"].widget = formish.Checkbox()


    def save(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        del data["terms"]
        account=Account(**data)
        session=meta.Session()
        session.add(account)
        session.flush()
        return account


    def __call__(self):
        if self.request.method=="POST":
            if self.request.POST["action"]=="cancel":
                return HTTPFound(location=route_url("home", self.request))
            account=self.save()
            if account:
                response=HTTPFound(location=route_url("dashboard", self.request))
                loginUser(account, self.request, response)
                return response
        
        return render("signup.pt", self.request, 
                status_int=202 if self.request.method=="POST" else 200,
                view=self,
                action_url=route_url("signup", self.request))
