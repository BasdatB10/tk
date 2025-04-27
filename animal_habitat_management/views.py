from django.shortcuts import render

def animal(request):
    return render(request, "animal.html")

def habitat(request):
    return render(request, "habitat.html")

def habitat_detail(request):
    return render(request, "habitat_detail.html")