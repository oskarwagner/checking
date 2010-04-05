import pkg_resources
from repoze.bfg.configuration import Configurator
from repoze.tm import TM


def resolve(name):
    return pkg_resources.EntryPoint.parse("x=%s" % name).load(False)


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


def setupRoutes(config):
    from repoze.bfg.view import append_slash_notfound_view
    config.set_notfound_view(append_slash_notfound_view)
    config.set_forbidden_view(resolve("checking.authentication:Forbidden"))
    config.add_static_view("behaviour", path="templates/behaviour")
    config.add_static_view("libraries", path="templates/libraries")
    config.add_static_view("style", path="templates/style")
    config.add_route("login", path="/login", view=resolve("checking.authentication:Login"))
    config.add_route("logout", path="/logout", view=resolve("checking.authentication:Logout"))


def app(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    if not settings.get('sqlalchemy.url'):
        raise ValueError("No 'sqlalchemy.url' value in application configuration.")
    config = Configurator(settings=settings)
    config.begin()
    setupSqlalchemy(settings)
    setupRoutes(config)
    config.end()

    app = config.make_wsgi_app()
    app = TM(app)

    return app



