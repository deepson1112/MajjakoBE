from django.db import models

from user.models import User
from retail.models import RetailProducts, RetailProductsVariations

from retail_wishlist.models import SharedRetailWishlist

# Create your models here.

class RetailCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="retail_carts")
    retail_product_variation = models.ForeignKey(RetailProductsVariations, on_delete=models.PROTECT, related_name="retail_carts")
    cart_id = models.CharField(max_length = 50, null=True)
    special_request = models.CharField(max_length=255, null=True, blank=True)
    receiver_name = models.TextField(null=True)
    active = models.BooleanField(default=True)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    shared_wishlist = models.ForeignKey(SharedRetailWishlist, on_delete=models.PROTECT, null=True)
    buy_now = models.BooleanField(default=False, null=True, blank=True)

    def __unicode__(self):
        return self.user


class RetailDeliveryCharge(models.Model):
    min_distance = models.IntegerField(default=0)
    max_distance = models.IntegerField(default=0)
    delivery_charge = models.FloatField(default=0.0)
    status = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)