from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from retail.models import RetailProducts
from retail_orders.views import StandardResultsSetPagination
from retail_review.filters import ReviewFilter
from retail_review.serializers import AverageReviewSerializer, UserReviewSerializer
from utils.permissions_override import IsVendor, IsSuperAdmin
from rest_framework.response import Response

from rest_framework.filters import SearchFilter
from retail_review.models import Review

# Create your views here.

class UserReviewViewSet(ModelViewSet):
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = UserReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter

    def get_queryset(self):
        return Review.objects.filter(is_approved=True, user=self.request.user).order_by('-created_date')

class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.filter(is_approved=True).order_by('-updated_date')
    serializer_class = UserReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter
    http_method_names = ['get', 'patch', 'put']
    pagination_class = StandardResultsSetPagination

class AverageReviewViewSet(ModelViewSet):
    queryset = RetailProducts.objects.filter(disabled=False, is_complete=True)
    serializer_class = AverageReviewSerializer
    http_method_names = ['get']

class VendorReviewViewSet(ModelViewSet):
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = UserReviewSerializer
    permission_classes =[IsVendor]

    def get_queryset(self):
        return Review.objects.filter(ordered_product__product_variation__product__vendor__user = self.request.user)


class AdminReviewViewSet(ModelViewSet):
    queryset = Review.objects.all().order_by('-created_date')
    serializer_class = UserReviewSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ReviewFilter
    http_method_names = ['get', 'patch', 'put']
    search_fields = ['ordered_product__product_variation__product__name', 'user__username', 'user__first_name', 'user__last_name']
    permission_classes = [IsSuperAdmin]

    def retrieve(self, request, *args, **kwargs):
        review_instance = self.get_object()
        review_instance.seen = True
        review_instance.save()
        serializer = self.get_serializer(review_instance)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()

        queryset = self.filter_queryset(self.get_queryset())
        unseen_count = queryset.filter(seen=False).count()

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            paginated_response.data['unseen_count'] = unseen_count
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'unseen_count': unseen_count,
            'results': serializer.data
        })