import io
import logging
import os
from validatish import validator
from validatish.error import Invalid
import formish
import schemaish
import PIL.Image
import sqlalchemy.types
from repoze.bfg.exceptions import Forbidden
from checking.model import meta
from checking.model.account import Account
from checking.utils import checkCSRF
from checking import _

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



class Image(validator.Validator):
    """Verify if an uploaded file is a valid image. It tries to load an image
    using PIL to see if it can be processed.
    """
    msg = _(u"Please upload an image. Supported formats are jpeg, png and gif.")
    msg_format = _(u"This image format is not supported. Please upload a jpeg, png or gif image.")

    def __call__(self, v):
        if v is None:
            return

        # The formish file manager gives us its cache file which starts
        # with internal data. PIL does not like that, so we need to create
        # our own file.
        position=v.file.tell()
        data=io.BytesIO(v.file.read())
        v.file.seek(position, os.SEEK_SET)

        try:
            pil_data=PIL.Image.open(data)
            pil_data.load()
        except (IOError, OverflowError):
            raise Invalid(self.msg_format, validator=self)

        if pil_data.format not in [ "GIF", "PNG", "JPEG" ]:
            raise Invalid(self.msg_format, validator=self)


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

    def validate(self, request, failure_callable=None, success_callable=None,
                 skip_read_only_defaults=False, check_form_name=True):
        if not checkCSRF(request):
            raise Forbidden("Invalid CSRF token")

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


