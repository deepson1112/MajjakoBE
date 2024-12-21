from django.contrib import admin

from retail_marketplace.models import RetailCart, RetailDeliveryCharge

# Register your models here.
admin.site.register(RetailCart)
admin.site.register(RetailDeliveryCharge)