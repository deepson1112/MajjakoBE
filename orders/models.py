from django.db import models
from offers.models import Coupons, LoyaltyPrograms
from user.models import User
from menu.models import Customization, FoodItem
from vendor.models import Vendor
from vendor.models import Vendor
import json
from datetime import datetime


class Payment(models.Model):
    PAYMENT_METHOD = (
        ('PayPal', 'PayPal'),
        ('RazorPay', 'RazorPay'),
        ('Stripe','Stripe')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.CharField(choices=PAYMENT_METHOD, max_length=100)
    amount = models.CharField(max_length=10)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


class PaymentInfo(models.Model):
    payment = models.ForeignKey( Payment ,on_delete=models.PROTECT, null=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    card_last4 = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=50, null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_email = models.CharField(max_length=255, null=True, blank=True)
    customer_phone = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, blank=True, null=True)
    vendors = models.ManyToManyField(Vendor, blank=True)
    order_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=50)
    
    address = models.CharField(max_length=200)
    country = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200)
    pin_code = models.CharField(max_length=10)
    order_payment_code = models.TextField(null=True, blank=True)
    
    total = models.FloatField()
    
    tax_data = models.JSONField(
        blank=True, help_text="Data format: {'tax_type':{'tax_percentage':'tax_amount'}}", null=True)
    total_data = models.JSONField(blank=True, null=True)
    
    total_tax = models.FloatField()
    
    delivery_charge = models.FloatField(null=True, blank=True)
    tip = models.FloatField(default=0, null=True)
    delivery_date = models.DateTimeField(default=datetime.now)

    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS, default='New')
    payment_method = models.CharField(max_length=25)
    updated_at = models.DateTimeField(auto_now=True)
    loyalty_program = models.ForeignKey(LoyaltyPrograms, on_delete = models.PROTECT, related_name="loyalty_orders", null=True)
    loyalty_points_received = models.FloatField(default = 0.0)

    def __str__(self):
        return self.order_number


class VendorsOrders(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="vendor_orders")
    order = models.ForeignKey(Order, on_delete = models.CASCADE, related_name='order_vendor')
    coupon_used = models.ForeignKey(Coupons, on_delete=models.CASCADE, related_name = "coupon_used", null=True)
    total_amount = models.FloatField(default=0.0)
    discounted_amount =models.FloatField(default=0.0)
    addons_cost = models.FloatField(default=0.0)
    total_tax = models.FloatField(default=0.0)


class OrderedFood(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_foods")
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, blank=True, null=True)
    cart_id = models.CharField(max_length = 50, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vendor_order = models.ForeignKey(VendorsOrders,null=True, on_delete=models.PROTECT, related_name = 'ordered_food')
    receiver_name = models.CharField(default="")

    def __str__(self):
        return self.food_item.food_title


class OrderCustomization(models.Model):
    customization = models.ForeignKey(
        Customization, on_delete=models.CASCADE, related_name="order_customization", null=True)
    amount = models.FloatField()
    description = models.CharField(max_length=255)
    food = models.ForeignKey(
        OrderedFood, null=True, on_delete=models.CASCADE, related_name='order_food_addons')
    order_customization = models.ForeignKey(
        Order, on_delete=models.CASCADE, null=True, related_name = "customizations")
    quantity = models.FloatField(default = 0.0)


class VendorInvoices(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor = models.ForeignKey(Vendor, null=True, related_name = "vendor_invoices", on_delete=models.CASCADE)
    ordered_food = models.ManyToManyField(OrderedFood)
    subtotal = models.FloatField()
    total_tax = models.FloatField(default=0.0)
    grand_total = models.FloatField()
    total_discount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.order.order_number)


class OrdersTaxDetails(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    tax_amount = models.DecimalField(decimal_places=2, max_digits=12)
    tax_rate = models.FloatField()
    vendor_sub_total = models.DecimalField(decimal_places=2, max_digits=12)
    created_date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self) -> str:
        return self.vendor.vendor_name + " : " + str(self.tax_amount)
