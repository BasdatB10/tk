from django.shortcuts import render, redirect
from django.contrib.auth import logout

def home(request):
    return render(request, "home.html")

def register(request):
    return render(request, "register.html")

def login(request):
    return render(request, "login.html")

def profile(request):
    return render(request, "profile.html")

def profile_dokter(request):
    return render(request, "profile_dokter.html")

def profile_pengunjung(request):
    return render(request, "profile_pengunjung.html")

def profile_staff(request):
    return render(request, "profile_staff.html")

def logout_view(request):
    logout(request)
    return redirect('base:home')