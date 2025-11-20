# api/views.py
from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import Vendor, Profile # <-- IMPORT THE MODELS

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save() # The form's save method now handles creating the Profile
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'api/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'api/login.html', {'form': form})


@login_required
def home(request):
    vendors = []
    user_university = None
    try:
        user_university = request.user.profile.university

        vendors = Vendor.objects.filter(university=user_university)
    except Profile.DoesNotExist:
      
        messages.warning(request, 'Your profile is incomplete. Please contact support.')
    
    context = {
        'vendors': vendors,
        'user_university': user_university
    }
    return render(request, 'api/home.html', context)

@login_required
def vendor_menu(request, vendor_id):

    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    menu_items = vendor.menu_items.all()
    
    context = {
        'vendor': vendor,
        'menu_items': menu_items
    }
    return render(request, 'api/menu.html', context)