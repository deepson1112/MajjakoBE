from rest_framework.routers import DefaultRouter
from django.urls import path


from retail_refund.views import RetailRefundViewSet, cancel_refund, AdminRefundStatusUpdateViewset, VendorRefundViewSet, RefundProductStatusViewSet, AdminRefundStatusViewSet

router = DefaultRouter()

# user
router.register("retail-refund", RetailRefundViewSet, basename="retail-refund")
router.register("update-refund-status",AdminRefundStatusUpdateViewset, basename="update-refund-status" )
router.register("vendor-refund-products", VendorRefundViewSet, basename="vendor-refund-products")
router.register("refund-product-status", RefundProductStatusViewSet, basename="refund-product-status")


#ADMIN

router.register("admin/refund-status", AdminRefundStatusViewSet, basename="refund-status")


urlpatterns = [
    path('cancel-refund/<int:refund_id>/item/<int:product_variation_id>/', cancel_refund)
] + router.urls
