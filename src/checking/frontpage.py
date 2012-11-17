from repoze.bfg.url import route_url
from checking.utils import render


def View(request):
    return render("frontpage.pt", request,
            login_url=route_url("login", request))

