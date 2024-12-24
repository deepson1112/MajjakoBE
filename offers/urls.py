from rest_framework.routers import DefaultRouter

from offers.views import DeleteSaveOnItemsDiscountPercentageView, DisableGetOneFreeOfferView, DisableSaveOnItemsOfferView, DisableStoreOfferView, GetOneFreeOfferViewSet, SaveOnItemsOfferViewSet, StoreOfferViewSet, ViewAvailableCouponsViewSet, ViewLoyaltyPrograms

router =DefaultRouter()


router.register('store-offer', StoreOfferViewSet, basename="store-offer")
router.register('get-one-free-offer', GetOneFreeOfferViewSet, basename="get-one-free-offer")
router.register('save-on-items', SaveOnItemsOfferViewSet, basename='save-on-items')

router.register('disable-store-offer', DisableStoreOfferView, basename= 'disable-store-offer')
router.register('disable-get-one-free-offer', DisableGetOneFreeOfferView, basename= 'disable-get-one-free-offer')
router.register('disable-save-on-items-offer', DisableSaveOnItemsOfferView, basename = 'disable-save-on-items-offer')

router.register('delete-food-items',DeleteSaveOnItemsDiscountPercentageView, basename='delete-food-items')
router.register('view-available-coupons',ViewAvailableCouponsViewSet, basename='view-available-coupons')
router.register('loyalty-programs',ViewLoyaltyPrograms, basename='loyalty-programs')

urlpatterns = router.urls