from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from menu.models import FoodItem, VendorCategories
from menu.retail_serializers import RetailSerializer
from menu.user_categoty_serializer import UserSideVendorCategoriesSerializer
from utils.permissions_override import IsRetail, IsVendor
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny

class RetailItemsViewSet(ModelViewSet):
    queryset = FoodItem.objects.filter(vendor__vendor_type = 2)
    serializer_class = RetailSerializer
    permission_classes = [IsRetail]

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)


class GetRetailItemsViewSet(ModelViewSet):
    queryset = FoodItem.objects.filter(vendor__vendor_type = 2)
    serializer_class = RetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["vendor_categories", "vendor",'vendor__vendor_type','vendor__offerings']
    http_method_names = ['get']

    

class UserSideRetailVendorCategoryViewSet(ReadOnlyModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = UserSideVendorCategoriesSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["department", "vendor",'vendor__vendor_type']


    def get_queryset(self):
        return VendorCategories.objects.all().filter(vendor__vendor_type=2)
