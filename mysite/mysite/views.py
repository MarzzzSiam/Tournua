from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

def login(request):
    return render(request, 'login.html')

def signUp(request):
    return render(request, 'signup.html')

