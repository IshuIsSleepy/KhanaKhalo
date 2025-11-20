# api/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='api/logout.html'), name='logout'),
    path('vendor/<int:vendor_id>/', views.vendor_menu, name='vendor_menu'),
    path('create-order/', views.create_order, name='create_order'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
]