from django.db import models
from datetime import datetime

from retail.models import RetailProductsVariations
from retail_logistics.models import DeliveryDriver
from retail_marketplace.models import RetailCart
from retail_offers.models import RetailCoupon, RetailLoyaltyPrograms
from user.models import User
from vendor.models import Vendor

# Create your models here.

class RetailPayment(models.Model):
    PAYMENT_METHOD = (
        ('Stripe','Stripe'),
        ('Esewa', 'Esewa'),
        ('Cash On Delivery', 'Cash On Delivery')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.CharField(choices=PAYMENT_METHOD, max_length=100)
    amount = models.CharField(max_length=10)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


class RetailPaymentInfo(models.Model):
    payment = models.ForeignKey( RetailPayment ,on_delete=models.PROTECT, null=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    card_last4 = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=50, null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_email = models.CharField(max_length=255, null=True, blank=True)
    customer_phone = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RetailOrder(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    NATION = (
        ('NP', 'NP'),
        ('US', 'US'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(
        RetailPayment, on_delete=models.SET_NULL, blank=True, null=True)
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
    pin_code = models.CharField(max_length=10, null=True, blank=True)
    order_payment_code = models.TextField(null=True, blank=True)
    
    total = models.FloatField()
    
    tax_data = models.JSONField(
        blank=True, help_text="Data format: {'tax_type':{'tax_percentage':'tax_amount'}}", null=True)
    
    total_data = models.JSONField(blank=True, null=True)
    
    total_tax = models.FloatField()
    
    delivery_charge = models.FloatField(null=True, blank=True)
    # delivery_date = models.DateTimeField(default=datetime.now)

    is_ordered = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUS, default='New')
    payment_method = models.CharField(max_length=25)
    loyalty_points_received = models.FloatField(default = 0.0)

    cart_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    loyalty_program = models.ForeignKey(RetailLoyaltyPrograms, on_delete = models.PROTECT, related_name="retail_loyalty_orders", null=True)

    carts = models.ManyToManyField(RetailCart, related_name="orders")

    nation = models.CharField(max_length=5, choices=NATION, default="NP", null=True, blank=True)

    def __str__(self):
        return self.order_number

class RetailVendorOrder(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="vendor_retail_orders")
    order = models.ForeignKey(RetailOrder, on_delete = models.CASCADE, related_name='retail_order_vendor')
    coupon_used = models.ForeignKey(RetailCoupon, on_delete=models.CASCADE, related_name = "retail_coupon_used", null=True)
    sub_total = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    total_discount_amount =models.FloatField(default=0.0)
    total_tax = models.FloatField(default=0.0)
    vendor_coupon_discount = models.FloatField(default=0.0)
    admin_coupon_discount = models.FloatField(default=0.0)
    loyalty_discount_amount = models.FloatField(default=0.0)
    delivery_charge = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return str(self.vendor.id)

class OrderedProduct(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    order = models.ForeignKey(RetailOrder, on_delete=models.CASCADE, related_name="order_products")
    product_variation = models.ForeignKey(RetailProductsVariations, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    discount_amount = models.FloatField()
    discounted_amount = models.FloatField()
    tax_rate = models.FloatField()
    tax_exclusive_amount = models.FloatField()

    vendor_order = models.ForeignKey(RetailVendorOrder, on_delete=models.CASCADE, related_name="ordered_product")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ordered_product_status = models.CharField(max_length=15, choices=STATUS, default='New', null=True, blank=True)

    seen = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return self.product_variation.product.name

class OrderStatus(models.Model):
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_code = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.status

class OrderedProductStatus(models.Model):
    ordered_product = models.ForeignKey(OrderedProduct, on_delete=models.CASCADE, related_name="status")
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_driver = models.ForeignKey(DeliveryDriver, on_delete=models.CASCADE, related_name='product_status', null=True, blank=True)
    closed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_status')

    def __str__(self) -> str:
        return self.ordered_product.product_variation.product.name
    
