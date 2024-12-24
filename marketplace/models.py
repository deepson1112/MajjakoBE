# import stripe
from django.db import models

from user.models import User
from menu.models import Customization, FoodItem
from vendor.models import Vendor


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    fooditem = models.ForeignKey(FoodItem, on_delete=models.PROTECT)
    cart_id = models.CharField(max_length = 50, null=True)
    special_request = models.CharField(max_length=255, null=True)
    receiver_name = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    quantity = models.IntegerField(default=1)

    def __unicode__(self):
        return self.user


class FoodCustomizations(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.PROTECT, related_name = "cart_addons")
    customization = models.ForeignKey(
        Customization, on_delete=models.PROTECT, related_name="cart_menu", null=True)
    
    # special_request = models.CharField(max_length=255)
    # receiver_name = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=1)





