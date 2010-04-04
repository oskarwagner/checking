from sqlalchemy import schema
from sqlalchemy import types
from checking.model.meta import BaseObject

class Currency(BaseObject):
    """A currency

    Currencies are identified by their ISO 4217 three letter currency
    code.
    """
    __tablename__ = "currency"

    code = schema.Column(types.String(3), primary_key=True)
    rate = schema.Column(types.Numeric(precision=6, scale=2), nullable=False)

    def __repr__(self):
        return "<Currency %s rate=%.2f>" % (self.code, self.rate)

