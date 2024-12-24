from django.db import models

from retail.models import RetailProductsVariations
from retail_logistics.models import DeliveryDriver
from retail_orders.models import RetailOrder
from user.models import User

# Create your models here.

class RetailRefundItem(models.Model):
    product_variation = models.ForeignKey(RetailProductsVariations, on_delete=models.CASCADE, related_name='product_refund')
    quantity = models.IntegerField(default=1)
    reason = models.TextField(null=True, blank=True)
    image_1 = models.ImageField(upload_to='refund-products/', null=True)
    image_2 = models.ImageField(upload_to='refund-products/', null=True, blank=True)
    image_3 = models.ImageField(upload_to='refund-products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.product_variation.product.name

class RetailRefund(models.Model):
    order = models.ForeignKey(RetailOrder, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refund_products = models.ManyToManyField(RetailRefundItem, related_name='refunds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

class RefundStatus(models.Model):
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.status

class RefundProductStatus(models.Model):
    refund_product = models.ForeignKey(RetailRefundItem, on_delete=models.CASCADE, related_name="refund_status")
    status = models.ForeignKey(RefundStatus, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_driver = models.ForeignKey(DeliveryDriver, on_delete=models.CASCADE, related_name='refund_status', null=True, blank=True)
    closed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_status')

    def __str__(self) -> str:
        return self.status.status