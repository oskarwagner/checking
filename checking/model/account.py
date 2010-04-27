from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types
from repoze.bfg import security
from checking.utils import randomString
from checking.model.meta import BaseObject


class Account(BaseObject):
    __tablename__ = "account"

    id = schema.Column(types.Integer(),
            schema.Sequence("account_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    login = schema.Column(types.String(32), nullable=False, unique=True)
    firstname = schema.Column(types.Unicode(32), nullable=False)
    surname = schema.Column(types.Unicode(64), nullable=False)
    email = schema.Column(types.String(256), nullable=False)
    password = schema.Column(types.String(256), nullable=False)
    secret = schema.Column(types.String(32))
    next_invoice_number = schema.Column(types.Integer(),
            nullable=False, default=1)

    def __repr__(self):
        return "<Account login=%s>" % self.login

    def authenticate(self, password):
        return password==self.password

    @property
    def title(self):
        """Return the title for this user. This is the full name of the user as
        should be used in the user interface.
        """
        if self.firstname and self.surname:
            return u"%s %s" % (self.firstname, self.surname)
        elif self.firstname:
            return self.firstname
        elif self.surname:
            return self.surname
        else:
            return self.login


    def processLogin(self):
        """Perform any tasks associated with a login. This will update the
        CSRF secret and log the login.

        .. todo:: login logging is not implemented yet
        """
        self.secret = randomString(32)


    @orm.reconstructor
    def _add_acls(self):
        self.__acl__ = [(security.Allow, self.id, ["view", "edit"]) ]

