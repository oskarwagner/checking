import logging
import os.path
import random
import pytz
import babel
import babel.support
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.url import route_url
from repoze.bfg.url import static_url
from checking.model import meta
from checking.model.currency import Currency

log = logging.getLogger(__name__)

timezone = pytz.timezone("Europe/Amsterdam")
locale = babel.Locale("en", "GB")
formatter = babel.support.Format(locale, timezone)


def isInt(id):
    try:
        id = int(id)
    except ValueError:
        return False
    else:
        return True



def randomString(length=32):
    """Return 32 bytes of random data. Only characters which do not require
    special escaping in HTML are generated."""

    safe_characters = "abcdefghijklmnopqrstuvwxyz" \
                      "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
                      "1234567890-/+"
    output = []
    append = output.append
    for i in xrange(length):
        append(random.choice(safe_characters))
    return "".join(output)



def checkCSRF(request):
    """Check if the request has a valid CSRF token."""
    from checking.authentication import currentUser

    user = currentUser(request)
    if user is None:
        return True

    token = request.POST.getall("csrf_token")
    if [user.secret]==token:
        return True

    log.warning("Invalid CSRF token from account %s (id=%d): %r",
                user.login, user.id, token)
    return False


def SimpleTypeFactory(cls):
    """A context factory-factory for models that have a simple id.
    """
    def factory(request):
        id = request.matchdict.get("id")
        if id is None:
            raise NotFound("Missing id")
        if not isInt(id):
            raise NotFound("Invalid id")

        result = meta.Session.query(cls).get(id)
        if result is None:
            raise NotFound("Unknown id")
        return result
    return factory



class Tools(object):
    def __init__(self, request):
        from checking.authentication import currentUser
        self.request=request
        self.user=currentUser(request)

    @property
    def csrf_token(self):
        """Return a CSRF token. For authenticated users this should be included
        in all forms under the name `csrf_token`."""
        if self.user is None:
            return None
        return self.user.secret


    def static_url(self, resource, **kw):
        """Generate a URL for a static resources. `path` is a filesystem path
        to the source, relatives to the `templates` directory.
        """
        return static_url("templates/%s" % resource, self.request, **kw)


    def route_url(self, name, *args, **kw):
        return route_url(name, self.request, *args, **kw)


    def currencies(self):
        return meta.Session.query(Currency.code, Currency.rate)\
                .filter(Currency.until==None)\
                .order_by(Currency.code).all()



def GlobalsFactory(system):
    """Globals factory to add extra globals to the variables passed to
    a template.

    This method should be registered using
    :py:meth:`repoze.bfg.configuration.Configurator.set_renderer_globals_factory`.
    """
    request=system["request"]
    return { "tools": Tools(request),
             "locale": locale,
             "formatter": formatter,
             "layout": get_template(os.path.join("templates", "layout.pt")),
           }


def render(name, request, context=None, status_int=None, view=None, section=None, **kw):
    if os.path.sep!="/":
        name=name.replace("/", os.path.sep)
    template=os.path.join("templates", name)

    response=render_template_to_response(template,
                request=request, context=context, view=view, section=section,
                layout=get_template(os.path.join("templates", "layout.pt")),
                **kw)
    if status_int is not None:
        response.status_int=status_int
    return response


