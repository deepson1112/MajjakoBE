from django.shortcuts import render
from requests import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser

from .models import OfferCategory, PlatformOffer, RetailCoupon, RetailLoyaltyPrograms, RetailSaveOnItemsDiscountPercentage, RetailStoreOffer, RetailGetOneFreeOffer, RetailSaveOnItemsOffer, VendorPlatformOffer
from .serializers import AdminOfferCategorySerializer, CreateMultipleVendorPlatformOfferSerializer, DetailVendorPlatformOfferSerializer, DisablePlatformOfferSerializer, DisableRetailCouponSerializer, DisableRetailGetOneFreeOfferSerializer, DisableRetailLoyaltyProgramsSerializer, DisableRetailSaveOnItemsOfferSerializer, DisableRetailStoreOfferSerializer, OfferCategorySerializer, PlatformOfferProductSerializer, PlatformOfferSerializer, ReatilStoreOfferSerializer, RetailCouponSerializer, RetailGetOneFreeOfferSerializer, RetailLoyaltyProgramsSerializer, RetailSaveOnItemsDiscountPercentageSerializer, RetailSaveOnItemsOfferSerializer, VendorPlatformOfferSerializer

from utils.permissions_override import IsSuperAdmin, IsVendor
from rest_framework.permissions import  IsAuthenticated

# Create your views here.


class RetailStoreOfferViewSet(ModelViewSet):
    queryset =RetailStoreOffer.objects.filter( disabled=False)
    serializer_class = ReatilStoreOfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor','audience']
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        if self.request.user.role == 1:
            return RetailStoreOffer.objects.filter(vendor__user = self.request.user, disabled=False)
        return RetailStoreOffer.objects.filter( disabled=False)
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
    
        data['created_by'] = request.user.id
        if request.user.role == 1:
            data['vendor'] = request.user.user.id

        request._full_data = data
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

class RetailGetOneFreeOfferViewset(ModelViewSet):
    queryset = RetailGetOneFreeOffer.objects.filter(disabled=False)
    serializer_class = RetailGetOneFreeOfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor']
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        if self.request.user.role == 1:
            return RetailGetOneFreeOffer.objects.filter(vendor__user = self.request.user, disabled=False)
        return RetailGetOneFreeOffer.objects.filter(disabled=False)
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
    
        data['created_by'] = request.user.id
        if request.user.role == 1:
            data['vendor'] = request.user.user.id

        request._full_data = data
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


from rest_framework.request import Request
from drf_yasg.utils import swagger_auto_schema
 
class RetailSaveOnItemsOfferViewSet(ModelViewSet):
    queryset = RetailSaveOnItemsOffer.objects.filter(disabled=False)
    serializer_class = RetailSaveOnItemsOfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor']
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    swagger_fake_view = True
 
    def get_queryset(self):
        if self.request.user.role == 1:
            return RetailSaveOnItemsOffer.objects.filter(vendor__user = self.request.user, disabled=False)
        return RetailSaveOnItemsOffer.objects.filter(disabled=False)
 
    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
    
        data['created_by'] = request.user.id
        if request.user.role == 1:
            data['vendor'] = request.user.user.id
 
        request._full_data = data
        return super().create(request, *args, **kwargs)
 
    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(auto_schema=None)
    def partial_update(self, request, *args, **kwargs):
        discount = request.data.pop("offer_items","")
        discount_create = []
        for each_discount in discount:
            if each_discount.get("id", False):
                order_detail_instance = RetailSaveOnItemsDiscountPercentage.objects.get(
                    id=each_discount["id"])
                serializer = RetailSaveOnItemsDiscountPercentageSerializer(
                    order_detail_instance, data=each_discount, partial=True
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                discount_create.append(each_discount)
        request.data['discount_percentage'] = discount_create
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class DisableRetailStoreOfferView(ModelViewSet):
    queryset = RetailStoreOffer.objects.filter(disabled=False)
    serializer_class = DisableRetailStoreOfferSerializer
    http_method_names = ['patch']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)
    

class DisableRetailGetOneFreeOfferView(ModelViewSet):
    queryset = RetailGetOneFreeOffer.objects.filter(disabled=False)
    serializer_class = DisableRetailGetOneFreeOfferSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)

class DisableRetailSaveOnItemsOfferView(ModelViewSet):
    queryset = RetailSaveOnItemsOffer.objects.filter(disabled=False)
    serializer_class = DisableRetailSaveOnItemsOfferSerializer
    http_method_names = ['patch']
    
    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)


class DeleteRetailSaveOnItemsDiscountPercentageView(ModelViewSet):
    queryset = RetailSaveOnItemsDiscountPercentage.objects.all()
    serializer_class = RetailSaveOnItemsDiscountPercentageSerializer

    http_method_names = ['delete']

class RetailCouponViewSet(ModelViewSet):
    queryset = RetailCoupon.objects.filter(disabled=False)
    serializer_class = RetailCouponSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsVendor]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        data = request.data
        if request.user.role == 1:
            data['vendor'] = ([request.user.user.id])
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user, disabled=False)
    
from rest_framework.response import Response

class RetailViewLoyaltyPrograms(ModelViewSet):
    queryset = RetailLoyaltyPrograms.objects.filter(disabled=False)
    serializer_class = RetailLoyaltyProgramsSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [IsSuperAdmin]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        if request.user.guest_user:
            return Response({"message": "Join our loyalty program by Signing Up and get exciting discounts"}, status=status.HTTP_200_OK)
        return super(RetailViewLoyaltyPrograms, self).list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(RetailViewLoyaltyPrograms, self).get_serializer_context()
        context['request'] = self.request
        return context


class OfferCategoryViewSet(ModelViewSet):
    queryset = OfferCategory.objects.all()
    serializer_class = OfferCategorySerializer
    permission_classes = [IsVendor]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return OfferCategory.objects.filter(vendor__user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

class PlatformOfferViewSet(ModelViewSet):
    queryset = PlatformOffer.objects.filter(disabled=False)
    serializer_class = PlatformOfferSerializer
    permission_classes = [IsSuperAdmin]
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

class VendorPlatformOfferViewSet(ModelViewSet):
    queryset = VendorPlatformOffer.objects.filter(platform_offer__disabled=False)
    serializer_class = DetailVendorPlatformOfferSerializer
    permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["platform_offer"]

    def get_queryset(self):
        return VendorPlatformOffer.objects.filter(vendor__user = self.request.user, platform_offer__disabled=False) 

    def get_serializer_class(self):
        if self.request.method=='POST':
            return CreateMultipleVendorPlatformOfferSerializer
        return super().get_serializer_class()

class PlatformOfferProductViewSet(ModelViewSet):
    queryset = PlatformOffer.objects.filter(disabled=False)
    serializer_class = PlatformOfferProductSerializer
    http_method_names = ['get']

class DisablePlatformOfferView(ModelViewSet):
    queryset = PlatformOffer.objects.filter(disabled=False)
    serializer_class = DisablePlatformOfferSerializer
    http_method_names = ['patch']


class DisableRetailCouponView(ModelViewSet):
    queryset = RetailCoupon.objects.filter(disabled=False)
    serializer_class = DisableRetailCouponSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)

class DisableRetailLoyaltyProgramsView(ModelViewSet):
    queryset = RetailLoyaltyPrograms.objects.filter(disabled=False)
    serializer_class = DisableRetailLoyaltyProgramsSerializer
    http_method_names = ['patch']


##ADMIN
    
class AdminOfferCategoryViewSet(ModelViewSet):
    queryset = OfferCategory.objects.all()
    serializer_class = AdminOfferCategorySerializer
    permission_classes = [IsSuperAdmin]
    parser_classes = (MultiPartParser, FormParser)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)