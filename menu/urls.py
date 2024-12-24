from django.urls import path, include
from rest_framework.routers import DefaultRouter
from menu.retail_views import GetRetailItemsViewSet, RetailItemsViewSet, UserSideRetailVendorCategoryViewSet
from menu.serializers import ChangeOrderDepartmentOrderSerializer, EnableVendorCategorySerializer

from menu.views import AddAddonsToFoodItemsViewSet, \
    AddFoodAddOnsCategoryViewSet, AddFoodItemsForeVendorsViewSet,\
    AddSecondaryCustomizationViewSet, ChangeOrderCategoriesViewSet, ChangeOrderFoodItemViewSet, ChangeOrderOfCustomizationViewSet, ChangeOrderingOfAddons, \
    CreateFoodItemsViewSet, DiscountVendorCategoryViewSet, EnableVendorCategoryView, FoodAddonsCategoryViews, \
    FoodAddonsViews, FoodItemViews, NestedFoodAddonsCategoryView, \
    RemoveAddonsToFoodItemsViewSet, RemoveFoodCustomization, RemoveSecondaryCustomizationViewSet, UserSideVendorCategoryViewSet, \
    VendorCategoryViewSet, VendorDepartmentViewSet, ChangeOrderDepartmentsVIewSet

router =DefaultRouter()

# router.register('food-category', CategoryViews)
# router.register('food-addons', FoodAddonsViews)

router.register('food-item-views', FoodItemViews, basename='food-item-views')

router.register('food-addons-category', FoodAddonsCategoryViews, basename='food-addons-category')

router.register('nested-food-addons', NestedFoodAddonsCategoryView,basename='nested-food-addons')

router.register('food', CreateFoodItemsViewSet, basename='food')

router.register('vendor-department', VendorDepartmentViewSet, basename='vendor-department')

router.register('vendor-category', VendorCategoryViewSet, basename='vendor-category')

router.register('user-vendor-category', UserSideVendorCategoryViewSet, basename='user-vendor-category')

router.register('discount-vendor-category', DiscountVendorCategoryViewSet, basename='discount-vendor-category')

# router.register('change-category-order', ChangeOrderCategoriesViewSet, basename='change-category-order')

router.register('change-food-order', ChangeOrderFoodItemViewSet, basename='change-food-order')

router.register('change-customization-order', ChangeOrderOfCustomizationViewSet, basename='change-customization-order')

router.register('enable-vendor-category', EnableVendorCategoryView, basename='enable-vendor-category')


# Urls for Vendors
router.register("add-food-items", AddFoodItemsForeVendorsViewSet, basename="add-food-items")

router.register("add-food-customization-title", AddFoodAddOnsCategoryViewSet, basename="add-food-customization-title")

router.register("add-food-customization-title-to-items", AddAddonsToFoodItemsViewSet, basename="add-food-customization-title-to-items")

router.register("remove-food-customization-title-from-items", RemoveAddonsToFoodItemsViewSet, basename="remove-food-customization-title-from-items")

router.register("add-secondary-customization", AddSecondaryCustomizationViewSet, basename="add-secondary-customization")

router.register("remove-secondary-customization", RemoveSecondaryCustomizationViewSet, basename="remove-secondary-customization")

router.register("change-order-of-customization", ChangeOrderingOfAddons, basename="change-order-of-customization")

router.register("remove-food-customization",RemoveFoodCustomization,basename="remove-food-customization")


# These are the retail items
router.register("retail-items",RetailItemsViewSet, basename='retails')
router.register("get-retail-items",GetRetailItemsViewSet, basename='get-retails')
router.register('user-vendor-retail-category', UserSideRetailVendorCategoryViewSet, basename="user-vendor-retail-category")


urlpatterns = [
    path('change-category-order/', ChangeOrderCategoriesViewSet.as_view()),
    path('change-department-order/', ChangeOrderDepartmentsVIewSet.as_view())
    ] +    router.urls
