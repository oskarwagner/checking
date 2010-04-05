from repoze.bfg.configuration import Configurator
from repoze.tm import TM


def setupSqlalchemy(config):
    """Setup the connection to the SQL server. The `options`
    parameter is a dictionary with the configuration options,
    which can include SQLAlchemy options prefixed with
    `sqlalchemy`. At a minimum `sqlalchemy.url` must be
    specified.
    """
    from zope.sqlalchemy import ZopeTransactionExtension
    from sqlalchemy import engine_from_config
    from sqlalchemy import orm
    from checking.model import meta

    sm = orm.sessionmaker(extension=ZopeTransactionExtension())
    engine = engine_from_config(config, "sqlalchemy.")
    meta.Session = orm.scoped_session(sm)
    meta.Session.configure(bind=engine)



def app(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    if not settings.get('sqlalchemy.url'):
        raise ValueError("No 'sqlalchemy.url' value in application configuration.")
    setupSqlalchemy(settings)
    config = Configurator(settings=settings)
    config.begin()
    config.load_zcml(zcml_file)
    config.end()
    app = config.make_wsgi_app()
    app = TM(app)



