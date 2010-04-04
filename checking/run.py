import transaction

from repoze.bfg.configuration import Configurator
from repoze.tm import after_end
from repoze.tm import isActive

from checking.models import DBSession
from checking.models import setup_engine

def handle_teardown(event):
    environ = event.request.environ
    if isActive(environ):
        t = transaction.get()
        after_end.register(DBSession.remove, t)

def app(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    if not settings.get('sqlalchemy.url'):
        raise ValueError("No 'sqlalchemy.url' value in application configuration.")
    setup_engine(settings)
    config = Configurator(settings=settings)
    config.begin()
    config.load_zcml(zcml_file)
    config.end()
    return config.make_wsgi_app()

