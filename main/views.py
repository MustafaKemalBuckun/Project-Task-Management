from django.shortcuts import render
from accounts.models import User

# Create your views here.


def index(request):
    context = {
        'users': User.objects.all(),
    }
    return render(request, 'home/index.html', context)
