import os.path
import random
import pytz
import babel
import babel.support
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.url import route_url
from repoze.bfg.url import static_url

timezone = pytz.timezone("Europe/Amsterdam")
locale = babel.Locale("nl", "NL")
formatter = babel.support.Format(locale, timezone)


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



def render(name, request, context=None, status_int=None, view=None, **kw):
    if os.path.sep!="/":
        name=name.replace("/", os.path.sep)
    template=os.path.join("templates", name)

    response=render_template_to_response(template,
                request=request, context=context, view=view,
                tools=Tools(request),
                formatter=formatter,
                layout=get_template(os.path.join("templates", "layout.pt")),
                **kw)
    if status_int is not None:
        response.status_int=status_int
    return response


