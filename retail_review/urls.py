from rest_framework.routers import DefaultRouter
from django.urls import path

from retail_review.views import UserReviewViewSet, ReviewViewSet, AverageReviewViewSet, VendorReviewViewSet, AdminReviewViewSet

router = DefaultRouter()

router.register("user-review", UserReviewViewSet, basename='user-review')
router.register("review", ReviewViewSet, basename='review')
router.register("average-review", AverageReviewViewSet, basename='average-review')
router.register("vendor-review", VendorReviewViewSet, basename='vendor-review')
router.register("admin-review", AdminReviewViewSet, basename="admin-review")

urlpatterns = router.urls