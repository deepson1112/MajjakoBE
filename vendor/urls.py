from rest_framework.routers import DefaultRouter

from vendor.views import FAQSViewSet, OfferingsViewSet, OpeningHourViews, VendorHoursViews, VendorViews

router = DefaultRouter()

router.register(
    'vendor', VendorViews
)

router.register('opening-hours', OpeningHourViews)
router.register('offerings-list', OfferingsViewSet)
router.register('vendor-timelines', VendorHoursViews)
router.register('faqs', FAQSViewSet)

urlpatterns = router.urls
