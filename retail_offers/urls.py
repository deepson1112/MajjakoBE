from rest_framework.routers import DefaultRouter

from .views import AdminOfferCategoryViewSet, DeleteRetailSaveOnItemsDiscountPercentageView, DisablePlatformOfferView, DisableRetailGetOneFreeOfferView, DisableRetailLoyaltyProgramsView, DisableRetailSaveOnItemsOfferView, DisableRetailStoreOfferView, PlatformOfferProductViewSet, PlatformOfferViewSet, RetailStoreOfferViewSet, RetailGetOneFreeOfferViewset, RetailSaveOnItemsOfferViewSet, RetailCouponViewSet, RetailViewLoyaltyPrograms, OfferCategoryViewSet, VendorPlatformOfferViewSet, DisableRetailCouponView

router =DefaultRouter()

router.register("retail-store-offer", RetailStoreOfferViewSet, basename="retail-store-offer")
router.register("retail-get-one-free-offer", RetailGetOneFreeOfferViewset, basename="retail-get-one-free-offer")
router.register("retail-save-on-item-offer", RetailSaveOnItemsOfferViewSet, basename="retail-save-on-item-offer")

router.register('disable-retail-store-offer', DisableRetailStoreOfferView, basename= 'disable-retail-store-offer')
router.register('disable-retail-get-one-free-offer', DisableRetailGetOneFreeOfferView, basename= 'disable-retail-get-one-free-offer')
router.register('disable-retail-save-on-items-offer', DisableRetailSaveOnItemsOfferView, basename = 'disable-retail-save-on-items-offer')
router.register('disable-retail-coupon', DisableRetailCouponView, basename='disable-retail-coupon')
router.register('disable-retail-loyalty-programs', DisableRetailLoyaltyProgramsView, basename='disable-retail-loyalty-programs')
router.register('disable-platform-offer', DisablePlatformOfferView, basename='disable-platform-offer')

router.register('delete-retail-products',DeleteRetailSaveOnItemsDiscountPercentageView, basename='delete-retail-products')

router.register('retail-coupon', RetailCouponViewSet, basename='retail-coupon')
router.register('retail-loyalty-programs',RetailViewLoyaltyPrograms, basename='loyalty-programs')

router.register('vendor/offer_category', OfferCategoryViewSet, basename='vendor_offer_vategory')

router.register('vendor/platform_offer', VendorPlatformOfferViewSet, basename='vendor_platform_offer')

router.register('platform_offer/products', PlatformOfferProductViewSet)

##ADMIN
router.register('admin/offer_category', AdminOfferCategoryViewSet, basename='admin_offer_vategory')
router.register('admin/platform_offer', PlatformOfferViewSet, basename='admin_platform_offer')

urlpatterns = router.urls