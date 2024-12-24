from django.db import models
import uuid

from retail.models import RetailProductsVariations
from user.models import User

# Create your models here.

class RetailWishList(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="retail_wishlists")
    retail_product_variation = models.ForeignKey(RetailProductsVariations, on_delete=models.PROTECT, related_name="retail_wishlists")
    wishlist_id = models.CharField(max_length = 50, null=True)
    special_request = models.CharField(max_length=255, null=True)
    receiver_name = models.TextField(null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=1, null=True, blank=True)

class SharedRetailWishlist(models.Model):
    wishlists = models.ManyToManyField(RetailWishList)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=12)

    address = models.CharField(max_length=250)

    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=6, null=True, blank=True)
    latitude = models.CharField(max_length=50)
    longitude = models.CharField(max_length=50)
    nation = models.CharField(max_length=5, default="NP", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class UserRetailWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'user_wishlist')
    wishlist = models.ForeignKey(RetailWishList,on_delete=models.CASCADE, related_name = 'user_wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)