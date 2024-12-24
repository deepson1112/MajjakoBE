from django.shortcuts import render
from rest_framework import viewsets

from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from rest_framework import status

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from retail_orders.views import StandardResultsSetPagination
from retail_refund.filters import RetailRefundFilter
from utils.permissions_override import IsSuperAdmin, IsVendor
from rest_framework.filters import SearchFilter

from retail_refund.models import RefundProductStatus, RefundStatus, RetailRefund, RetailRefundItem
from retail_refund.serializers import RefundProductStatusSerializer, RefundStatusSerializer, RetailRefundItemSerializer, RetailRefundSerializer

from drf_yasg.utils import swagger_auto_schema
 
 
class RetailRefundViewSet(viewsets.ModelViewSet):
    queryset = RetailRefund.objects.all()
    serializer_class = RetailRefundSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['order__order_number', 'refund_products__product_variation__product__name']
    filterset_class = RetailRefundFilter
    http_method_names = ['post', 'get']
    parser_classes = (MultiPartParser, FormParser)
    swagger_fake_view = True
    pagination_class = StandardResultsSetPagination
 
    @swagger_auto_schema(auto_schema=None)
    def retrieve(self, request, *args, **kwargs):
         return super().retrieve(request, *args, **kwargs)
 
    @swagger_auto_schema(auto_schema=None)
    def list(self, request, *args, **kwargs):
         return super().list(request, *args, **kwargs)
    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
         return super().create(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def cancel_refund(self, refund_id, product_variation_id):
    try:
        refund = RetailRefund.objects.get(id=refund_id)
        refund_item = refund.refund_products.get(product_variation=product_variation_id)
        refund_item.status = 'cancelled'
        refund_item.save()

        return Response({"message": "Refund for product canceled successfully."}, status=status.HTTP_200_OK)
    
    except RetailRefund.DoesNotExist:
            return Response({"message": "Invalid refund"}, status=status.HTTP_404_NOT_FOUND)
    
    except RetailRefundItem.DoesNotExist:
            return Response({"message": "Invalid refund item"}, status=status.HTTP_404_NOT_FOUND)

class AdminRefundStatusUpdateViewset(viewsets.ModelViewSet):
    queryset = RetailRefundItem.objects.all()
    serializer_class = RetailRefundItemSerializer
    http_method_names = ['patch', 'get']
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['refunds__order']

    def get_queryset(self):
        return  RetailRefundItem.objects.filter(refunds__user=self.request.user).order_by('id')

class VendorRefundViewSet(viewsets.ModelViewSet):
    queryset = RetailRefundItem.objects.all()
    serializer_class = RetailRefundItemSerializer
    http_method_names = ['get']
    permission_classes = [IsVendor]

    def get_queryset(self):
        user = self.request.user
        vendor_id = user.user.id
        return RetailRefundItem.objects.filter(product_variation__product__vendor__user=self.request.user)

class RefundProductStatusViewSet(viewsets.ModelViewSet):
    queryset = RefundProductStatus.objects.all()
    serializer_class = RefundProductStatusSerializer


#ADMIN
    
class AdminRefundStatusViewSet(viewsets.ModelViewSet):
    queryset = RefundStatus.objects.all()
    serializer_class = RefundStatusSerializer
    permission_classes = [IsSuperAdmin]