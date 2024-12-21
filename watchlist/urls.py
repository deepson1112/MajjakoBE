from rest_framework.routers import DefaultRouter

from watchlist.views import UserWatchListViewSet

router = DefaultRouter()

router.register('user-watchlist', UserWatchListViewSet, basename='user-watchlist')

urlpatterns = router.urls
