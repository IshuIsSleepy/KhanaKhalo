from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=100, unique=True , null = True)
    address = models.CharField(max_length=255, blank=True)
    logo_url = models.URLField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    roll_no = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture_url = models.URLField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Vendor(models.Model):
    # --- NEW: Link a Vendor to a User (The Shop Owner) ---
    # This allows a user to login and see the "Vendor Dashboard"
    vendor_owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='managed_vendor', null=True, blank=True)

    class ServiceType(models.TextChoices):
        RESTAURANT = 'RESTAURANT', 'Restaurant'
        CAFE = 'CAFE', 'Cafe'
        DHABA = 'DHABA', 'Dhaba'
        STALL = 'STALL', 'Small Stall'
        BRAND = 'BRAND', 'Big Brand (e.g., Domino\'s)'

    class DietaryFocus(models.TextChoices):
        VEG_ONLY = 'VEG_ONLY', 'Pure Veg'
        NON_VEG = 'NON_VEG', 'Non-Veg Available'
        BOTH = 'BOTH', 'Veg & Non-Veg'

    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255) 
    description = models.TextField(blank=True, help_text="A short, catchy description of the vendor.")
    image_url = models.URLField(max_length=255, blank=True, null=True)

    opening_time = models.TimeField()
    closing_time = models.TimeField()
    vendor_type = models.CharField(max_length=20, choices=ServiceType.choices, default=ServiceType.STALL)
    dietary_focus = models.CharField(max_length=20, choices=DietaryFocus.choices, default=DietaryFocus.BOTH)

    offers_delivery = models.BooleanField(default=False)
    offers_takeaway = models.BooleanField(default=True)
    has_seating = models.BooleanField(default=False)
    is_delivering_now = models.BooleanField(default=False)

    current_orders = models.PositiveIntegerField(default=0)
    max_orders = models.PositiveIntegerField(default=10)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_open(self):
        now = timezone.localtime(timezone.now()).time()
        return self.opening_time <= now <= self.closing_time

    @property
    def crowd_status(self):
        if self.max_orders == 0: return "Not Available"
        ratio = self.current_orders / self.max_orders
        if ratio >= 0.8: return "Very Crowded"
        elif ratio >= 0.5: return "Moderately Crowded"
        else: return "Not Crowded"

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='menu_items' , null = True)
    category = models.CharField(max_length=50, default="General")
    name = models.CharField(max_length=100)
    short_description = models.TextField(blank=True)
    image_url = models.URLField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_veg = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    options = models.JSONField(blank=True, null=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.vendor.name}"

# --- NEW MODELS FOR ORDERING SYSTEM ---

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        ACCEPTED = 'ACCEPTED', 'Cooking / Processing'
        READY = 'READY', 'Ready for Pickup'
        COMPLETED = 'COMPLETED', 'Completed'
        REJECTED = 'REJECTED', 'Rejected'

    class OrderMethod(models.TextChoices):
        PICKUP = 'PICKUP', 'Pickup'
        DELIVERY = 'DELIVERY', 'Delivery'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders')
    
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    order_method = models.CharField(max_length=10, choices=OrderMethod.choices, default=OrderMethod.PICKUP)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2) # Price at time of order
    # We store options as a simple text string for now (e.g., "Extra Cheese, No Mayo")
    # You could use JSONField if you wanted to be fancy, but TextField is safer for quick dev.
    customization = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, blank=True, null=True)
    rating = models.PositiveIntegerField() 
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(vendor__isnull=False) | models.Q(item__isnull=False),
                name='review_must_be_for_vendor_or_item'
            )
        ]