from rest_framework.routers import DefaultRouter

from .views import ContactViewSet, AdminContactViewSet

router = DefaultRouter()

router.register("contact", ContactViewSet, basename="contact")
router.register("admin-contact", AdminContactViewSet, basename="admin-contact")


urlpatterns = router.urls