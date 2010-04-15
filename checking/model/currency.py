from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy.sql import functions
from checking.model.meta import BaseObject

class Currency(BaseObject):
    """A currency

    Currencies are identified by their ISO 4217 three letter currency
    code.
    """
    __tablename__ = "currency"

    id = schema.Column(types.Integer(),
            schema.Sequence("currency_id_seq", optional=True),
            primary_key=True, autoincrement=True)
    code = schema.Column(types.String(3), nullable=False)
    rate = schema.Column(types.Numeric(precision=6, scale=2), nullable=False)
    when = schema.Column(types.Date(), nullable=False, default=functions.now())

    def __repr__(self):
        return "<Currency id=%s, code=%s rate=%.2f>" % (self.id, self.code, self.rate)

