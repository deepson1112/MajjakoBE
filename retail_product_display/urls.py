from rest_framework.routers import DefaultRouter

from .views import CategoryGroupProductDisplayViewSet, CategoryGroupViewSet

router = DefaultRouter()

router.register('group-category-products', CategoryGroupProductDisplayViewSet, basename='group-category-products')
router.register('category_group', CategoryGroupViewSet, basename='category_group')

urlpatterns = router.urls
