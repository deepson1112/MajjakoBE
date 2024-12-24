from rest_framework.routers import DefaultRouter

from orders.views import ConfirmOrderView, OrderTaxDetailsViewSet, OrdersViewSet, PaymentViewSet, VendorInvoicesViewSet, VendorOrdersViewSet

router = DefaultRouter()

router.register('payments', PaymentViewSet)

router.register('orders',OrdersViewSet, basename='orders')

router.register('vendor-orders',VendorOrdersViewSet,basename='vendor-orders')

router.register('confirm_payment' ,ConfirmOrderView,basename='confirm_payment')

router.register('vendor-invoices',VendorInvoicesViewSet, basename='vendor-invoices')

router.register('order-tax-details',OrderTaxDetailsViewSet,basename='order-tax-details')


urlpatterns = router.urls
