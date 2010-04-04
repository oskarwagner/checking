from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Model(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)



def setup_engine(config):
    """Setup the connection to the SQL server. The `options`
    parameter is a dictionary with the configuration options,
    which can include SQLAlchemy options prefixed with
    `sqlalchemy`. At a minimum `sqlalchemy.url` must be
    specified.
    """
    engine = engine_from_config(config, "sqlalchemy.")
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

