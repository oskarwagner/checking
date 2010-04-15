import logging
from validatish import validator
from validatish.error import Invalid
import formish
import schemaish
import sqlalchemy.types
from checking.authentication import currentUser
from checking.model import meta
from checking.model.account import Account

log = logging.getLogger(__name__)


class AvailableLogin(validator.Validator):
    """Check if a login name is available."""
    msg = u"This login is already in use."

    def __call__(self, v):
        if v is None:
            return

        query=meta.Session.query(Account.id).filter(Account.login==v)
        if query.count():
            raise Invalid(self.msg, validator=self)


class MustAgree(validator.Required):
    """This is a stronger version of the standard `Required` validator.
    """
    msg = u"You must agree to the terms and conditions."

    def __call__(self, v):
        if not v:
            raise Invalid(self.msg, validator=self)


class Form(formish.Form):
    def get_field(self, *name):
        name = ".".join(name)
        return formish.Form.get_field(self, name)

    def keys(self, *name):
        field = self.get_field(*name)
        groups = list(field.collection_fields())
        return [ group.name for group in groups]



class CSRFForm(Form):
    """Base class for forms which verifies CSRF tokens. Tokens have
    to be passed in as a HTTP POST parameter called `csrf_token`.
    GET requests are not allowed to prevent tokens from appearing in
    proxy or webserver logfiles."""

    def checkCSRF(self, request):
        user = currentUser(request)
        if user is None:
            return True

        token = request.POST.getall("csrf_token")
        if [user.secret]==token:
            return True

        log.warning("Invalid CSRF token from account %s (id=%d): %r",
                    user.login, user.id, token)
        return False


    def validate(self, request, failure_callable=None, success_callable=None,
                 skip_read_only_defaults=False, check_form_name=True):
        if not self.checkCSRF(request):
            raise Exception("Invalid CSRF token")

        return super(CSRFForm, self).validate(request, failure_callable,
                                              success_callable,
                                              skip_read_only_defaults,
                                              check_form_name)



def OrmToSchema(klass, exclude=["id"]):
    schema=schemaish.Structure()
    typemap = {
            sqlalchemy.types.Boolean: schemaish.Boolean,
            sqlalchemy.types.Numeric: schemaish.Decimal,
            sqlalchemy.types.Integer: schemaish.Integer,
            sqlalchemy.types.String: schemaish.String,
            sqlalchemy.types.Unicode: schemaish.String,
            sqlalchemy.types.UnicodeText: schemaish.String,
            }

    columns=klass.__table__.c
    for id in klass.__table__.c.keys():
        if id in exclude:
            continue
        column=columns.get(id)
        fieldtype=typemap.get(type(column.type), None)
        if fieldtype is None:
            continue

        validators=[]
        if not column.nullable:
            validators.append(validator.Required())

        if isinstance(column.type, (sqlalchemy.types.String, sqlalchemy.types.Unicode)):
            if column.type.length:
                validators.append(validator.Length(max=column.type.length))

        if len(validators)>1:
            field=fieldtype(validator=validator.All(*validators))
        elif len(validators)==1:
            field=fieldtype(validator=validators[0])
        else:
            field=fieldtype()
        schema.add(id, field)

    return schema


