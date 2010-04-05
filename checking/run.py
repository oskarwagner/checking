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
    meta.metadata.bind=engine


def setupRoutes(config):
    from repoze.bfg.view import append_slash_notfound_view
    from checking.authentication import predAuthenticated
    from checking.authentication import predAnonymous
    config.set_notfound_view(append_slash_notfound_view)
    config.set_forbidden_view(resolve("checking.authentication:Forbidden"))
    config.add_static_view("behaviour", path="templates/behaviour")
    config.add_static_view("libraries", path="templates/libraries")
    config.add_static_view("style", path="templates/style")
    config.add_route("home", path="/", 
            custom_predicates=(predAnonymous,),
            view=resolve("checking.frontpage:View"))
    config.add_route("dashboard", path="/", 
            custom_predicates=(predAuthenticated,),
            view=resolve("checking.dashboard:View"))
    config.add_route("login", path="/login", view=resolve("checking.authentication:Login"))
    config.add_route("logout", path="/logout", view=resolve("checking.authentication:Logout"))

    factory=resolve("checking.customer:Factory")
    config.add_route("customers", path="/customers", view=resolve("checking.customer:Overview"))
    config.add_route("customer_add", path="/customers/add", view=resolve("checking.customer:Add"))
    config.add_route("customer_edit", path="/customers/:id/edit",
            factory=factory, view=resolve("checking.customer:Edit"),
            permission="edit")
    config.add_route("customer_view", path="/customers/:id",
            factory=factory, view=resolve("checking.customer:View"),
            permission="view")

#    factory=resolve("checking.customer:Factory")
    config.add_route("invoice_view", path="/invoices/:id",
#            factory=factory, view=resolve("checking.customer:View"),
            permission="view")

def setupChameleon(config):
    from checking.zpt import PermissionTranslator
    config.registry.registerUtility(
            PermissionTranslator(),
            name="permission")


def app(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    from repoze.bfg.authentication import AuthTktAuthenticationPolicy
    from checking.authorization import RouteAuthorizationPolicy
    from checking.authentication import verifyUser

    if not settings.get("sqlalchemy.url"):
        raise ValueError("No 'sqlalchemy.url' value in application configuration.")
    config = Configurator(settings=settings,
            authentication_policy=AuthTktAuthenticationPolicy("secret",
                callback=verifyUser,
                timeout=30*60, max_age=30*60,
                reissue_time=20*60),
            authorization_policy=RouteAuthorizationPolicy())
    config.begin()
    setupSqlalchemy(settings)
    setupRoutes(config)
    setupChameleon(config)
    config.hook_zca()
    config.end()

    app = config.make_wsgi_app()
    app = TM(app)

    return app



