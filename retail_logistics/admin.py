from django.contrib import admin

from .models import DeliveryDriverLocation, DeliveryDriverStatus, DeliveryDriver, DeliveryBoundary, DeliveryBoundaryKmlFile
# Register your models here.
admin.site.register(DeliveryDriverLocation)
admin.site.register(DeliveryDriverStatus)
admin.site.register(DeliveryDriver)
admin.site.register(DeliveryBoundaryKmlFile)
admin.site.register(DeliveryBoundary)