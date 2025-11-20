from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

from .forms import UserRegisterForm
from .models import Vendor, Profile, MenuItem, Order, OrderItem

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
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
                

                if hasattr(user, 'managed_vendor'):
                    return redirect('vendor_dashboard')
                    
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

    try:
        user_university = request.user.profile.university
        vendors = Vendor.objects.filter(university=user_university)
    except Profile.DoesNotExist:

        if hasattr(request.user, 'managed_vendor'):
            return redirect('vendor_dashboard')
        messages.warning(request, 'Your profile is incomplete.')
        vendors = []
        user_university = None
    
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


@login_required
def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vendor_id = data.get('vendor_id')
            cart_items = data.get('items')
            method = data.get('method', 'PICKUP')
            
            vendor = get_object_or_404(Vendor, id=vendor_id)
            

            order = Order.objects.create(
                user=request.user,
                vendor=vendor,
                total_amount=0,
                order_method=method.upper()
            )

            total = 0
            for item in cart_items:
                menu_item = MenuItem.objects.get(id=item['id'])
                item_price = menu_item.price 
                
                item_total = float(item_price) * item['quantity']
                total += item_total
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    price=item_price,
                    customization=json.dumps(item.get('options', []))
                )

            order.total_amount = total
            order.save()
            
            vendor.current_orders += 1
            vendor.save()

            return JsonResponse({'status': 'success', 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'api/my_orders.html', {'orders': orders})

@login_required
def vendor_dashboard(request):

    try:
        vendor = request.user.managed_vendor
        orders = Order.objects.filter(vendor=vendor).order_by('-created_at')
    except (Vendor.DoesNotExist, AttributeError):

        messages.error(request, "You do not have a vendor account assigned.")
        return redirect('home')
    
    return render(request, 'api/vendor_dashboard.html', {'orders': orders})

@login_required
@csrf_exempt
def update_order_status(request, order_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            order = get_object_or_404(Order, id=order_id)
            

            if request.user != order.vendor.vendor_owner:
                 return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

            previous_status = order.status
            order.status = new_status
            order.save()

            if new_status in ['COMPLETED', 'REJECTED'] and previous_status not in ['COMPLETED', 'REJECTED']:
                order.vendor.current_orders = max(0, order.vendor.current_orders - 1)
                order.vendor.save()
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)