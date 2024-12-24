from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import RetailCartViewSet, ClearRetailCartViewSet, UserRetailCartViewSet, RetailCartItemCalculationViewSet, CurrencyExchangeRateView

router = DefaultRouter()

router.register("retail-cart", RetailCartViewSet, basename="retail-cart")
router.register("clear-retail-cart",ClearRetailCartViewSet, basename="clear-retail-cart")
router.register("user-cart-detail", UserRetailCartViewSet, basename="user-cart-detail")
router.register("retail-sub-total-calculations", RetailCartItemCalculationViewSet, basename="retail-sub-total-calculations")

urlpatterns = [
    path('exchange-rate/',  CurrencyExchangeRateView.as_view())
] + router.urls