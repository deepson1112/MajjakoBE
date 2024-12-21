from django.contrib import admin

from retail_refund.models import RetailRefund, RetailRefundItem, RefundStatus, RefundProductStatus


class RefundProductStatusAdmin(admin.ModelAdmin):
    list_display = ('refund_product', 'status', 'created_by', 'description', 'delivery_driver', 'closed', 'created_at', 'updated_at')
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Register your models here.
admin.site.register(RetailRefund)
admin.site.register(RetailRefundItem)
admin.site.register(RefundStatus)
admin.site.register(RefundProductStatus, RefundProductStatusAdmin)
