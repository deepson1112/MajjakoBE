from django.urls import path
from rest_framework.routers import DefaultRouter

from retail_orders.views import ConfirmRetailOrderView, RetailOrdersViewSet, RetailPaymentViewSet, RetailVendorOrdersViewSet, OrderedProductViewSet, OrderedProductStatusViewSet, UserOrderedProductViewSet, AdminOrderStatusVIewSet, AdminOrderedProductStatusViewSet, AdminOrderedProductViewSet, CancelRetailOrderView, AnalyticsView, GroupedUserOrderedProductViewSet, UserRetailOrdersViewSet, AdminOrderedProductUnseenCountView

router = DefaultRouter()
router.register('retail-orders',RetailOrdersViewSet, basename='orders')
router.register('retail-payments', RetailPaymentViewSet, basename='retail-payments')
router.register('confirm-retail-payment' ,ConfirmRetailOrderView,basename='confirm-retail-payment')
router.register('cancel-retail-payment' ,CancelRetailOrderView,basename='cancel-retail-payment')
router.register('retail-vendor-orders',RetailVendorOrdersViewSet, basename='retail-vendor-orders')
router.register('ordered-product', OrderedProductViewSet, basename='ordered_product')
router.register('ordered-product-status', OrderedProductStatusViewSet, basename='ordered-product-status')

router.register('ordered-product-user', UserOrderedProductViewSet, basename='ordered_product-user')
router.register('grouped-ordered-product-user', GroupedUserOrderedProductViewSet, basename='grouped-ordered_product-user')

router.register('user-retail-orders', UserRetailOrdersViewSet, basename="user-retail-orders")


#ADMIN endpoint

router.register('admin-order-status', AdminOrderStatusVIewSet, basename='admin-order-status')
router.register('admin-ordered-product-status', AdminOrderedProductStatusViewSet, basename='admin-ordered-product-status')
router.register('admin-order-product', AdminOrderedProductViewSet, basename='admin-order-product')


urlpatterns = [
    path('analytics/',  AnalyticsView.as_view()),
    path('admin-order-product-count/', AdminOrderedProductUnseenCountView.as_view())
] + router.urls