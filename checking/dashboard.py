from checking.utils import render
from checking.authentication import currentUser


def View(request):
    return render("dashboard.pt", request,
            context=currentUser(request))


