import re
import os.path
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


def normalizeForUrl(input):
    normalizers = [
            ( re.compile(r"[ \\|/\(\)\[\]]"), "-"),
            ( re.compile(r"&"), "+" ),
            ( re.compile("-{2,}"), "-" ),
            ]
    output = input.lower()
    for (pattern, sub) in normalizers:
        output = pattern.sub(sub, output)
    return output


class Tools(object):
    debug = True

    def __init__(self, request):
        self.request=request

    def normalize(self, input):
        return normalizeForUrl(input)

    def static_url(self, resource, **kw):
        return static_url("templates/%s" % resource, self.request, **kw)

    def route_url(self, name, *args, **kw):
        return route_url(name, self.request, *args, **kw)

    @property
    def current_user(self):
        from checking.authentication import currentUser
        return currentUser(self.request)


def render(name, request, context=None, status_int=None, **kw):
    if os.path.sep!="/":
        name=name.replace("/", os.path.sep)
    template=os.path.join("templates", name)

    response=render_template_to_response(template,
                request=request, context=context,
                tools=Tools(request),
                formatter=formatter,
                layout=get_template(os.path.join("templates", "layout.pt")),
                **kw)
    if status_int is not None:
        response.status_int=status_int
    return response


