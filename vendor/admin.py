from django.contrib import admin

from vendor.models import FAQS, Offerings, Vendor, VendorHourTimelines

# Register your models here.
admin.site.register(VendorHourTimelines)

# admin.site.register(VendorProfile)

#display the name of the Offerings in admin panel
class OfferingsAdmin(admin.ModelAdmin):
    list_display = ['name']

class VendorAdmin(admin.ModelAdmin):
    list_display = ['vendor_name', 'vendor_location_latitude', 'vendor_location_longitude']

admin.site.register(Offerings, OfferingsAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(FAQS)

