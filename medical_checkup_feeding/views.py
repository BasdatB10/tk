from django.shortcuts import render, redirect

def medical_record(request):
    return render(request, 'medical_record.html')

def medical_checkup(request):
    return render(request, 'medical_checkup.html')

def feeding(request):
    return render(request, 'feeding.html')
