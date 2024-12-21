from typing import Any, Iterable
from django.db import models
from django.http import HttpResponse
from menu.models import FoodItem, VendorCategories
from user.models import User
# from rest_framework.exceptions import ValidationError
from vendor.models import Vendor
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Create your models here.

AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)

class StoreOffer(models.Model):
    AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)
    offer_name = models.CharField(max_length = 100, null=True)
    discount_percentages = models.FloatField(default=0)
    
    minimum_spend_amount = models.FloatField(default=0)
    maximum_redeem_value = models.FloatField(default=0, null=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')

    discount_banner = models.ImageField(upload_to="offers_banner/", null=True
                                        )
    active = models.BooleanField(default=True)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)


class GetOneFreeOffer(models.Model):
    AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)
    item = models.ManyToManyField(FoodItem)
    active = models.BooleanField(default=True)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')    
    
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    discount_banner = models.ImageField(upload_to="offers_banner/", null=True)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    offer_name = models.CharField(max_length = 255, null=True,default="")
    def __str__(self) -> str:
        return str(self.id)


class SaveOnItemsOffer(models.Model):
    AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')        
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    discount_banner = models.ImageField(upload_to="offers_banner/", null=True)
    
    offer_name = models.CharField(max_length = 255, null=True)
    def __str__(self) -> str:
        return str(self.id)


class SaveOnItemsDiscountPercentage(models.Model):
    store_offer = models.ForeignKey(SaveOnItemsOffer, on_delete=models.CASCADE, related_name = "offer_items")
    discount_percentages = models.FloatField(default=0)
    item = models.ForeignKey(FoodItem, null=True, on_delete=models.PROTECT, related_name="save_on_item")
    category = models.ForeignKey(VendorCategories, null=True, on_delete=models.PROTECT, related_name="save_on_item")


class FreeDelivery(models.Model):
    AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')      
    start_date = models.DateTimeField(null=True)
    discount_banner = models.ImageField(upload_to="offers_banner/", null=True)
    offer_name = models.CharField(max_length = 255, null=True, default="")
    end_date = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def clean(self):
        if FreeDelivery.objects.filter(start_date__lte=self.start_date, end_date__gte=self.end_date).exists():
            raise ValidationError(_('Free delivery on this time already exists'))


    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
    

    def __str__(self) -> str:
        return str(self.id)
    

class DeliveryCharge(models.Model):
    transaction_amount = models.FloatField(default=0.0)
    delivery_charge = models.FloatField(default=0.0)
    status = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    charge_name = models.CharField(max_length = 255)


class Coupons(models.Model):
    COUPON_TYPE = (
        ("Flat Discount","Flat Discount"),
        ("Percentage Off","Percentage Off"),
        ("Delivery Fee  off","Delivery Fee  off")
    )

    DISCOUNT_TYPE = (
        ("IN AMOUNT","IN AMOUNT"),
        ("IN PERCENTAGE","IN PERCENTAGE")
    )
    discount_amount = models.FloatField(default=0.0)
    discount_type = models.CharField(choices= DISCOUNT_TYPE, help_text = '''
        ("IN AMOUNT","IN AMOUNT"),
        ("IN PERCENTAGE","IN PERCENTAGE")
        ''', 
        default = 'IN AMOUNT'
    )
    discount_percentages = models.FloatField(default = 0.0)
    coupons_title = models.CharField(max_length=255)
    coupon_code = models.CharField(max_length = 25, help_text="max length = 25", unique=True)
    coupon_type = models.CharField(choices = COUPON_TYPE, help_text = '''
        ("Flat Discount","Flat Discount"),
        ("Percentage Off","Percentage Off"),
        ("Delivery Fee  off","Delivery Fee  off")
                                   ''')
    minimum_spend_amount = models.FloatField(default=0.0)
    maximum_redeem_amount = models.FloatField(default=0.0)
    
    limitation_for_user = models.IntegerField()
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    
    vendor = models.ForeignKey(Vendor,on_delete=models.PROTECT ,related_name="coupons", null=True)

    
class LoyaltyPrograms(models.Model):
    program_name = models.CharField(max_length=255)
    program_code = models.CharField(max_length = 255, unique = True, null=True)
    no_of_points = models.IntegerField()
    
    discount_percentages = models.FloatField(default = 0.0)
    
    maximum_redeem_amount = models.FloatField(default=0.0)
    
    minimum_spend_amount = models.FloatField(default=0.0)





class LoyaltySettings(models.Model):
    program_name = models.CharField(max_length=255)
    in_amount = models.FloatField(default=0.0, help_text="This is the minimum amount that can be converted to loyalty points")

    provided_points = models.FloatField(default=0.0, help_text="This is the amount that is provided per the amount transactions")
    
    converted_into = models.FloatField(default = 0.0, help_text="This is the amount that 1 loyalty points are converted into")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.program_name
