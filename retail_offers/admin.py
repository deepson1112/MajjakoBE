from django.contrib import admin

# Register your models here.
from .models import  VendorPlatformOffer, PlatformOffer, RetailStoreOffer, RetailGetOneFreeOffer, RetailSaveOnItemsOffer, RetailSaveOnItemsDiscountPercentage, RetailCoupon, RetailLoyaltyPrograms, OfferCategory, RetailFreeDelivery

admin.site.register(RetailStoreOffer)
admin.site.register(RetailGetOneFreeOffer)
admin.site.register(RetailSaveOnItemsOffer)
admin.site.register(RetailSaveOnItemsDiscountPercentage)
admin.site.register(RetailCoupon)
admin.site.register(RetailLoyaltyPrograms)
admin.site.register(OfferCategory)
admin.site.register(PlatformOffer)
admin.site.register(VendorPlatformOffer)
admin.site.register(RetailFreeDelivery)