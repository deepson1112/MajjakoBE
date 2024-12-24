from django.contrib import admin

from .models import RetailOrder, RetailPayment, RetailPaymentInfo, RetailVendorOrder, OrderedProduct, OrderStatus, OrderedProductStatus

class OrderProductStatusAdmin(admin.ModelAdmin):
    list_display = ('ordered_product', 'status', 'description', 'created_by', 'delivery_driver', 'closed', 'created_at', 'updated_at')
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Register your models here.
admin.site.register(RetailOrder)
admin.site.register(RetailPayment)
admin.site.register(RetailPaymentInfo)
admin.site.register(RetailVendorOrder)
admin.site.register(OrderedProduct)
admin.site.register(OrderStatus)
admin.site.register(OrderedProductStatus, OrderProductStatusAdmin)