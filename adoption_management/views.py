from django.shortcuts import render, redirect


def manage_adopt(request):
    return render(request, "manage_adopt.html")

def show_adopter_page(request):
    return render(request,"adopter_page.html")

def show_adopter_list(request):
    return render(request,"adopter_list.html")