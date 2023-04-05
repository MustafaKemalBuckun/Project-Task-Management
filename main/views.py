from django.shortcuts import render, redirect
from accounts.models import User
from .forms import UserRegisterForm
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# Create your views here.


def index(request):
    context = {
        'users': User.objects.all(),
    }
    return render(request, 'home/index.html', context)

def register(request):
   if request.method == 'POST':
       registerform = UserRegisterForm(request.POST)
       if registerform.is_valid():
           registerform.save()
           username = registerform.cleaned_data.get('username')
           messages.success(request, f'{username} kullanıcısı için hesap başarıyla oluşturuldu! Giriş yapabilirsiniz.')
           return redirect('login')
   else:
       registerform = UserRegisterForm()
   return render(request, 'accounts/register.html', {'registerform': registerform})

def login_view(request):
    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            print("test")
            username = loginform.cleaned_data.get("username")
            password = loginform.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        loginform = LoginForm(request.POST)
    return render(request, 'accounts/login.html', {'loginform': loginform})
