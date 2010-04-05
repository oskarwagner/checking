import formish
import schemaish
from webob.exc import HTTPFound
from validatish import validator
from repoze.bfg.interfaces import IAuthenticationPolicy
from repoze.bfg.url import route_url
from checking.model import meta
from checking.model import Account
from checking.utils import render

def verifyUser(identity, request):
    """User verification method. This method is called by during
    authentication to check if the user is valid. It should return `None` if
    the user is invalid, or a list of group ids if the user is valid.
    """
    try:
        identity = int(identity)
    except ValueError:
        return None

    id = meta.Session.query(Account.id).get(identity)
    if id is None:
        return None

    return []


def loginUser(account, request, response):
    """Start a login session for a user. This will update the response to
    set a cookie which authenticates the user on future requests.
    """
    account.processLogin()
    policy=request.registry.getUtility(IAuthenticationPolicy)
    headers=policy.remember(request, account.id)
    response.headers.update(headers)


def logoutUser(request, response):
    """Remove the login session for a user. This will update the response
    to delete the authentication cookie.
    """
    policy=request.registry.getUtility(IAuthenticationPolicy)
    headers=policy.forget(request)
    response.headers.update(headers)


def currentUser(request):
    """Return the currently :obj:`capos.model.account.Account` , or
    `None` if the current user is anonymous."""
    policy = request.registry.getUtility(IAuthenticationPolicy)
    userid = policy.authenticated_userid(request)
    if not userid:
        return None
    return meta.Session.query(Account).get(userid)


class LoginSchema(schemaish.Structure):
    login = schemaish.String(validator=validator.Required())
    password = schemaish.String(validator=validator.Required())
    came_from = schemaish.String()



class Login(object):
    def __init__(self, request):
        self.request=request
        self.form=formish.Form(LoginSchema())


    def login(self):
        try:
            data=self.form.validate(self.request)
        except formish.FormError:
            return False

        query = meta.Session.query(Account)
        account = query.filter(Account.login==data["login"]).first()
        if account and account.authenticate(data["password"]):
            return account

        return False


    def __call__(self):
        if self.request.method=="POST":
            account=self.login()
            if account:
                came_from=self.request.POST.get("came_from")
                if came_from:
                    response=HTTPFound(location=came_from)
                else:
                    response=HTTPFound(location=route_url("dashboard", self.request))
                loginUser(account, self.request, response)
                return response
        
        return render("login.pt", self.request,
                status_int=202 if self.request.method=="POST" else 200,
                login_url=route_url("login", self.request),
                form=self.form)


def Logout(request):
    response=HTTPFound(location=route_url("home", request))
    logoutUser(request, response)
    return response



def Forbidden(request):
    form = formish.Form(LoginSchema(), defaults=dict(came_from=request.url))
    return render("login.pt", request,
                login_url=route_url("login", request),
                form=form)


def predAuthenticated(context, request):
    """Route predicate to check if the user is authenticated.
    This method can be used in the custom_predicates parameter for
    route and view statements.
    """
    return currentUser(request) is not None



def predAnonymous(context, request):
    """Route predicate to check if the user is anoymous.
    This method can be used in the custom_predicates parameter for
    route and view statements.
    """
    return currentUser(request) is None

