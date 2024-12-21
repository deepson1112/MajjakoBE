from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import RetailWishListViewSet, SharedRetailWishlistViewSet, user_wishlist, delete_product_wislist

router = DefaultRouter()

router.register("retail-wishlist", RetailWishListViewSet, basename="retail-wishlist")
router.register("share-retail-wishlist",SharedRetailWishlistViewSet, basename="share-retail-wishlist" )

urlpatterns = [
    path('', include(router.urls)),
    path('user_wishlist/', user_wishlist), 
    path('delete_product_wislist/<variation_id>/', delete_product_wislist)
]