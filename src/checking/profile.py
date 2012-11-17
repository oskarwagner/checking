import formish
import schemaish
from validatish import validator
from webob.exc import HTTPFound
from repoze.bfg.url import route_url
from checking import form
from checking.authentication import currentUser
from checking.utils import render


class ProfileSchema(schemaish.Structure):
    firstname = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(max=64)))
    surname = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(max=64)))
    email = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(max=256),
        validator.Email()))
    password = schemaish.String(validator=validator.All(
        validator.Length(min=4, max=256),
        validator.Length(max=256)))

    company = schemaish.String(validator=validator.All(
        validator.Required(),
        validator.Length(max=64)))
    ein = schemaish.String()
    logo = schemaish.String(validator=form.Image())
    address = schemaish.String()
    postal_code = schemaish.String(validator=validator.Length(max=16))
    city = schemaish.String(validator=validator.Length(max=64))
    country = schemaish.String(validator=validator.Length(max=3))


def Factory(request):
    return currentUser(request)


class View(object):
    def __init__(self, context, request):
        self.context=context
        self.request=request
        self.form=form.CSRFForm(ProfileSchema(), defaults=self.context.__dict__)
        self.form["password"].widget=formish.CheckedPassword()
        self.form["logo"].widget=formish.FileUpload()


    def update(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        if data["password"] is not None:
            self.context.password=data["password"]
        del data["password"]
        if data["logo"] is not None:
            data["logo_mimetype"]=data["logo"].mimetype
            data["logo"]=data["logo"].file.read()
        else:
            del data["logo"]
        for (key,value) in data.items():
            setattr(self.context, key, value)
        return True


    def __call__(self):
        if self.request.method=="POST" and self.update():
            return HTTPFound(location=route_url("home", self.request))

        return render("profile.pt", self.request, context=self.context,
                status_int=202 if self.request.method=="POST" else 200,
                form=self.form,
                action_url=route_url("profile", self.request))

