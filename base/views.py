from django.shortcuts import render, redirect
from django.contrib.auth import logout

def home(request):
    return render(request, "home.html")

def register(request):
    return render(request, "register.html")

def login(request):
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('base:home')