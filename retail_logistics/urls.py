from rest_framework.routers import DefaultRouter

from .views import DeliveryDriverLocationViewSet, DeliveryDriverStatusViewSet, DeliveryDriverViewSet

router = DefaultRouter()

router.register("admin/delivery-driver-location", DeliveryDriverLocationViewSet, basename='admin-delivery-driver-location')
router.register("admin/delivery-driver-status", DeliveryDriverStatusViewSet)
router.register("admin/delivery-driver", DeliveryDriverViewSet)

urlpatterns = router.urls
