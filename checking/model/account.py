from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy.ext.declarative import synonym_for
from checking.model.meta import BaseObject


class Account(BaseObject):
    __tablename__ = "account"

    id = schema.Column(types.Integer(),
            schema.Sequence("account_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    firstname = schema.Column(types.Unicode(32), nullable=False)
    surname = schema.Column(types.Unicode(64), nullable=False)
    email = schema.Column(types.String(256), nullable=False, unique=True)
    password = schema.Column(types.String(256), nullable=False)

    @synonym_for("email")
    @property
    def login(self):
        return self.email

    def __repr__(self):
        return "<Account login=%s>" % self.email

    def authenticate(self, password):
        return password==self.password

    @property
    def title(self):
        return u"%s %s" % (self.firstname, self.surname)

