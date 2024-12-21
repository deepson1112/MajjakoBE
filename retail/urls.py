from rest_framework.routers import DefaultRouter
from django.urls import path

from retail import views

router = DefaultRouter()

router.register("retail-variation-types", views.RetailVariationTypeViewSet)
router.register("retail-variation", views.RetailVariationViewSet)
router.register("retail-products", views.RetailProductsViewSet)
router.register("retail-products-variation", views.RetailProductsVariationsViewSet)

router.register("product", views.NestedProductViewSet)

#User Side API
router.register("retail-categories", views.RetailCategoriesViewSet)
router.register("retail-sub-categories", views.RetailSubCategoriesViewSet)
router.register("sub-categories", views.DetailRetailSubCategoriesViewSet),
router.register("variations-image", views.ProductsVariationsImageViewSet)
router.register("retail-products-display", views.DisplayRetailProductsViewSet, basename="retail-products-display")

router.register("retail-product-list", views.RetailProductListViewSet, basename="retail-product-list")

router.register("refund-policy", views.RefundPolicyViewSet, basename="refund-policy")

router.register("product-request", views.ProductRequestViewSet, basename="product-request")


router.register("category", views.CategoryViewSet, basename="category")
router.register("sub-category", views.SubCategoryViewSet, basename="sub-category")

router.register("product-bulk-delete", views.ProductBulkDeleteView, basename='product-bulk-delete')

router.register("edit-product-get",views.EditProductView, basename='edit-product-get')

router.register("retail-vendor-category", views.VendorCategoryView, basename='retail-vendor-category')
router.register("retail-vendor-subcategory", views.VendorSubCategoryView, basename='retail-vendor-subcategory')


#ADMIN
router.register("admin/retail-variation", views.AdminRetailVariationViewSet, basename='admin-retail-variation')
router.register("admin/products", views.AdminNestedProductViewSet, basename="admin-products")
router.register("admin/retail-variation-type", views.AdminRetailVariationTypeViewSet, basename='retail-variation-type')
router.register("admin/product-request", views.AdminProductRequestViewSet, basename="admin-product-request")

urlpatterns = [
    path('upload-products/', views.CSVProductUploadView.as_view()),
    path('product-export/', views.CSVProductExportView.as_view()),
    path('clear-cache/', views.clear_cache, name='clear_cache'),
    path("price-change/", views.VendorPriceChange.as_view()),
    path('category-change/', views.CategoryChangeView.as_view()),
    path('add-vendor-description/', views.AddVendorDescriptionView.as_view())
] +  router.urls