from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from offers.models import Coupons, GetOneFreeOffer, LoyaltyPrograms, SaveOnItemsDiscountPercentage, SaveOnItemsOffer, StoreOffer
from offers.serializers import DisableGetOneFreeOfferSerializer, DisableSaveOnItemsOfferSerializer, DisableStoreOfferSerializer, GetOneFreeOfferSerializer, LoyaltyProgramsSerializer, SaveOnItemsDiscountPercentageSerializer, SaveOnItemsOfferSerializer, StoreOfferSerializer, ViewAvailableCouponsSerializer
from django_filters.rest_framework import DjangoFilterBackend
from utils.permissions_override import IsVendor, IsVendorOrReadOnly
# Create your views here.
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

class StoreOfferViewSet(ModelViewSet):
    queryset = StoreOffer.objects.all()
    serializer_class = StoreOfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor','audience']

    def get_queryset(self):
        return StoreOffer.objects.filter(vendor__user = self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsVendor]
        return super().get_permissions()


class GetOneFreeOfferViewSet(ModelViewSet):
    queryset = GetOneFreeOffer.objects.all()
    serializer_class = GetOneFreeOfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor']


    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsVendor]
        return super().get_permissions()
    

class SaveOnItemsOfferViewSet(ModelViewSet):
    queryset = SaveOnItemsOffer.objects.all()
    serializer_class = SaveOnItemsOfferSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor']

    
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsVendor]
        return super().get_permissions()
    
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        discount = request.data.pop("offer_items","")
        discount_create = []
        for each_discount in discount:
            if each_discount.get("id", False):
                order_detail_instance = SaveOnItemsDiscountPercentage.objects.get(
                    id=each_discount["id"])
                serializer = SaveOnItemsDiscountPercentageSerializer(
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


class DisableStoreOfferView(ModelViewSet):
    queryset = StoreOffer.objects.all()
    serializer_class = DisableStoreOfferSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)
    

class DisableGetOneFreeOfferView(ModelViewSet):
    queryset = GetOneFreeOffer.objects.all()
    serializer_class = DisableGetOneFreeOfferSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)

class DisableSaveOnItemsOfferView(ModelViewSet):
    queryset = SaveOnItemsOffer.objects.all()
    serializer_class = DisableSaveOnItemsOfferSerializer
    http_method_names = ['patch']
    
    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)
    
    
class DeleteSaveOnItemsDiscountPercentageView(ModelViewSet):
    queryset = SaveOnItemsDiscountPercentage.objects.all()
    serializer_class = SaveOnItemsDiscountPercentageSerializer

    http_method_names = ['delete']


class ViewAvailableCouponsViewSet(ModelViewSet):
    queryset = Coupons.objects.all()
    serializer_class = ViewAvailableCouponsSerializer
    http_method_names = ['get','post','patch','put']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        current_time = timezone.now()
        # print(self.action)
        if self.action == 'list':
            return super().get_queryset().filter(
                Q(start_date__lte=current_time, end_date__gte=current_time)
            )
        
        elif self.action == 'get_vendor_coupons':
            return super().get_queryset().filter(vendor__user = self.request.user)
        elif self.action == 'retrieve':
            return super().get_queryset().filter(vendor__user = self.request.user)
        elif self.action == 'update':
            return super().get_queryset().filter(vendor__user = self.request.user)
        else: 
            return 
    
    def get_permissions(self):
        if self.action == "get_vendor_coupons":
            return [IsVendor()]
        
        return [IsVendorOrReadOnly()]

    @action(detail=False, url_path='vendor_coupons', methods=['GET'])
    def get_vendor_coupons(self, request, *args, **kwargs):
        queryset = self.queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ViewAvailableCouponsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ViewAvailableCouponsSerializer(queryset, many=True)
        return Response(data = serializer.data)
    


class ViewLoyaltyPrograms(ReadOnlyModelViewSet):
    queryset = LoyaltyPrograms.objects.all()
    serializer_class = LoyaltyProgramsSerializer

    def get_serializer_context(self):
        context = super(ViewLoyaltyPrograms, self).get_serializer_context()
        context['request'] = self.request
        return context

