from rest_framework.routers import DefaultRouter

from .views import HomepageContentViewSet, AdsSectionViewSet


router = DefaultRouter()

router.register('content', HomepageContentViewSet, basename='content')
router.register('ads', AdsSectionViewSet, basename='ads')

urlpatterns = router.urls
