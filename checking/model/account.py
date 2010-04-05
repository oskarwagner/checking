from sqlalchemy import schema
from sqlalchemy import types
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

    def __repr__(self):
        return "<Account login=%s>" % self.login

    def authenticate(self, password):
        return password==self.password

    @property
    def title(self):
        return u"%s %s" % (self.firstname, self.surname)

