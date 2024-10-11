from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from .models import Volunteer
from django.contrib.auth.decorators import login_required

def volunteer_list(request):
    volunteers = Volunteer.objects.all()
    return render(request, 'uplift/volunteer_list.html', {'volunteers': volunteers})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'profile.html')

def home(request):
    return render(request, 'home.html')