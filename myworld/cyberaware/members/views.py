from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.template import loader
from .models import Member


def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('mainpage.html')
    context = {
        'mymembers': mymembers,
    }
    return HttpResponse(template.render(context, request))


def login_view(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("members")
        else:
            message = "Invalid login or password."

    return render(request, "login.html", {"message": message})

