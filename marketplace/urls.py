from rest_framework.routers import DefaultRouter

from marketplace.views import CartBreakDownViewSet, CartItemSCalculationViewSet, CartViewSet, ClearCartViewSet, ItemsQuantityInCart, UpdateCartQuantityViewSet, UpdateCartViewSet

router = DefaultRouter()

router.register("cart", CartViewSet, basename="carts")
router.register("clear-cart", ClearCartViewSet, basename="clear-carts")

router.register("update-quantity", UpdateCartViewSet, basename="update-quantity")
router.register("update-cart-quantity", UpdateCartQuantityViewSet, basename="update-cart-quantity")
router.register("cart-quantity", ItemsQuantityInCart, basename="cart-quantity")

router.register("cart-breakdown", CartBreakDownViewSet, basename="cart-breakdown")

router.register("sub_total_calculations", CartItemSCalculationViewSet, basename="calculations")

urlpatterns = router.urls