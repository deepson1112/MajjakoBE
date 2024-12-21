from decimal import Decimal
import os
import random
import chardet
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from menu.models import VendorCategories, VendorDepartment
from retail.models import ProductsVariationsImage, RetailProducts, RetailProductsVariations, RetailVariation, RetailVariationType
from retail.serializers import AdminNestedProductSerializer, AdminRetailVariationSerializer, AdminRetailVariationTypeSerializer, CategorySerializer, CreateMultipleProductVariationsSerializer, DetailRetailSubCategoriesSerializer, EditProductSerializer, NestedProductSerializer, ProductRequestSerializer, ProductsVariationsImageSerializer, RefundPolicySerializer, RetailCategoriesSerializer, RetailProductListSerializer, RetailProductsSerializer, RetailProductsVariationsSerializer, RetailSubCategoriesSerializer, RetailVariationSerializer, RetailVariationTypeSerializer, SubCategorySerializer 
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
import random
from hashlib import sha256
from django.db.models import F, Func

from rest_framework.exceptions import PermissionDenied


from rest_framework.permissions import IsAuthenticated

from retail_orders.views import StandardResultsSetPagination
from utils.permissions_override import IsSuperAdmin, IsVendor, IsVendorOrReadOnly
from django.db.models import Q, Count
from django_filters import FilterSet, BooleanFilter, NumberFilter

from utils.priority_search_filter import PrioritizedSearchFilter
from vendor.models import Vendor
from .models import ProductRequest, RefundPolicy, RetailProducts, RetailVariation, SearchKeyword, generate_sku

class RandomOrder(Func):
    function = 'MOD'
    template = '%(function)s(%(expressions)s, %(mod_value)s)'

class FilterForRetailProductsVariations(FilterSet):
    category = NumberFilter(method='filter_category', label='category')
    sub_category = NumberFilter(method='filter_sub_category', label='Price more than or equal to')

    class Meta:
        model = RetailVariationType
        fields = ['category', 'sub_category']

    def filter_category(self, queryset, name, value):
        if value:
            return queryset.filter(variation__products__product__category=value).distinct()
        return queryset

    def filter_sub_category(self, queryset, name, value):

        if value:
            return queryset.filter(variation__products__product__sub_category=value).distinct()
        return queryset
    


class RetailVariationTypeViewSet(ModelViewSet):
    queryset = RetailVariationType.objects.filter(disabled=False)
    serializer_class = RetailVariationTypeSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name']
    filterset_class = FilterForRetailProductsVariations
    permission_classes = [IsVendorOrReadOnly]
    

    def get_queryset(self):
        own = self.request.query_params.get("own", False)
        if own:
            return RetailVariationType.objects.filter(disabled=False, variation__products__product__vendor = self.request.user.user).distinct()
        return super().get_queryset()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        create_new_variation = []
        for each_data in data.get('variation', ""):

            if each_data.get("id",None):
                item = RetailVariation.objects.get(id= each_data['id'])
                update_serializer = RetailVariationSerializer(item, each_data,many=False,partial=True,
                                                                           context={"request":self.request})
                update_serializer.is_valid(raise_exception=True)
                update_serializer.save()
            else:
                create_new_variation.append(each_data)
        
        request.data['variation'] = create_new_variation
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.disabled = True
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class RetailVariationViewSet(ModelViewSet):
    queryset = RetailVariation.objects.filter(disabled=False)
    serializer_class = RetailVariationSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name']
    permission_classes = [IsVendor]
    filterset_fields = ['variation_type']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.disabled = True
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class RetailProductsViewSet(ModelViewSet):
    queryset = RetailProducts.objects.filter(disabled=False)
    serializer_class = RetailProductsSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsVendor]
    search_fields  = ['name']
    filterset_fields = ['category','sub_category','vendor']

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.disabled = True
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ProductsVariationsImageViewSet(ModelViewSet):
    queryset = ProductsVariationsImage.objects.all()
    serializer_class = ProductsVariationsImageSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsVendor]
    filterset_fields = ['variations']
    http_method_names = ['delete','post','get']

    def get_queryset(self):
        return ProductsVariationsImage.objects.filter(vendor__user = self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        image_path = instance.image.path
        response = super().destroy(request, *args, **kwargs)
        if os.path.exists(image_path):
            os.remove(image_path)
        return response


class RetailProductsVariationsViewSet(ModelViewSet):
    queryset = RetailProductsVariations.objects.filter(disabled=False)
    serializer_class = RetailProductsVariationsSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsVendor]
    search_fields  = ['product__name']
    filterset_fields = ['product','product__vendor','variation']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method=='POST':
            return CreateMultipleProductVariationsSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return self.queryset.filter(product__vendor__user = self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.disabled = True
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

##

class RetailCategoriesViewSet(ModelViewSet):
    queryset = VendorDepartment.objects.all()
    serializer_class = RetailCategoriesSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['department_name']
    http_method_names = ['get']
    filterset_fields = ['vendor']
    search_fields  = ['name']



    def get_queryset(self):
        return VendorDepartment.objects.filter(vendor_type = 2)
    

class RetailSubCategoriesViewSet(ModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = RetailSubCategoriesSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['department_name']
    filterset_fields = ['vendor', 'department']
    http_method_names = ['get']
    search_fields  = ['name']


    def get_queryset(self):
        return VendorCategories.objects.filter(vendor_type = 2)

class DetailRetailSubCategoriesViewSet(ModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = DetailRetailSubCategoriesSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['category_name']
    # filterset_fields = ['vendor', 'department']
    http_method_names = ['get']


    def get_queryset(self):
        queryset = VendorCategories.objects.filter(vendor_type=2, image__isnull=False).exclude(image="").order_by("?")

        limit = self.request.query_params.get('limit')
        vendor = self.request.query_params.get('vendor')
        department = self.request.query_params.get('department')

        if vendor:
            queryset = queryset.filter(vendor=vendor)
        
        if department:
            queryset = queryset.filter(department=department)

        if limit:
            try:
                limit = int(limit)
                if limit < 1:
                    raise ValidationError("'limit' must be a positive integer.")
            except ValueError:
                raise ValidationError("'limit' must be an integer.")
            
            queryset = queryset[:limit]

        return queryset


class FilterForRetailProducts(FilterSet):
    availability = BooleanFilter(method='filter_availability', label='Available in stock')
    minimum_price = NumberFilter(method='filter_minimum_price', label='Price more than or equal to')
    maximum_price = NumberFilter(method='filter_maximum_price', label='Price less than or equal to')
    variations = NumberFilter(method='filter_variations', label='Product Variations')
    category = NumberFilter(method='filter_category', label='Categories')
    sub_category = NumberFilter(method='filter_sub_category', label='Sub_categories')
    hide_product = NumberFilter(method='filter_product', label='Hide product')

    class Meta:
        model = RetailProducts
        fields = ['category', 'sub_category', 'vendor', 'availability', 'minimum_price', 'variations','maximum_price']

    def filter_product(self, queryset, name, value):
        if value:
            return queryset.exclude(id=value)
        return queryset

    def filter_availability(self, queryset, name, value):
        if value:
            return queryset.filter(products_variations__stock_quantity__gt=0).distinct()
        return queryset

    def filter_minimum_price(self, queryset, name, value):
        if value is not None:
            return queryset.filter(products_variations__price__gte=value).distinct()
        return queryset

    def filter_maximum_price(self, queryset, name, value):
        if value is not None:
            return queryset.filter(products_variations__price__lte=value).distinct()
        return queryset

    def filter_variations(self, queryset, name, value):
        if not value:
            return queryset

        variations = self.request.GET.getlist('variations')

        variation_type_groups = {}
        for variation_id in variations:
            try:
                variation = RetailVariation.objects.get(id=variation_id)
                variation_type_id = variation.variation_type.id
                if variation_type_id not in variation_type_groups:
                    variation_type_groups[variation_type_id] = []
                variation_type_groups[variation_type_id].append(variation_id)
            except RetailVariation.DoesNotExist:
                continue

        for variation_type_id, variation_ids in variation_type_groups.items():
            q_objects = Q()
            for variation_id in variation_ids:
                q_objects |= Q(products_variations__variation__id=variation_id)
            queryset = queryset.filter(q_objects).annotate(
                num_variations=Count('products_variations__variation')).filter(
                num_variations__gte=len(variation_type_groups))
        return queryset.distinct()

    def filter_category(self, queryset, name, value):
        if not value:
            return queryset

        categories = self.request.GET.getlist('category')
        queryset = queryset.filter(category__in=categories)
        return queryset

    def filter_sub_category(self, queryset, name, value):
        if not value:
            return queryset

        sub_categories = self.request.GET.getlist('sub_category')
        queryset = queryset.filter(sub_category__in=sub_categories)
        return queryset
    
from rest_framework.pagination import PageNumberPagination
from rest_framework.validators import ValidationError

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Prefetch

CACHE_TTL = None

class DisplayRetailProductsViewSet(ModelViewSet):
    queryset = RetailProducts.objects.select_related('category', 'sub_category', 'vendor').filter(disabled=False).prefetch_related(
        Prefetch(
            'products_variations',
            queryset=RetailProductsVariations.objects.filter(disabled=False),
        )
    )
    serializer_class = RetailProductsSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name']
    filterset_class = FilterForRetailProducts
    pagination_class = StandardResultsSetPagination
    # filterset_fields = ['category','sub_category','vendor',']
    http_method_names = ['get']
    
    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        cache_key = f"retail_product_{product.id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=CACHE_TTL)
        return response

class RetailProductListPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        page = request.query_params.get('page', None)

        if page is None:
            return None

        return super().paginate_queryset(queryset, request, view)

    def next_page_number(self):
        return self.page.number + 1 if self.page.has_next() else None

    def get_paginated_response(self, data):
        if self.page is None:
            return Response({'results': data})


        return Response({
            'next_page_number': self.next_page_number(),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })
#
# class RetailProductListViewSet(ModelViewSet):
#     queryset = RetailProducts.objects.filter(disabled=False).prefetch_related('products_variations')
#     serializer_class = RetailProductListSerializer
#     filter_backends = [PrioritizedSearchFilter, DjangoFilterBackend]
#     search_fields  = ['name', 'description', 'sub_category__category_name', 'category__department_name']
#     filterset_class = FilterForRetailProducts
#     pagination_class = RetailProductListPagination
#     http_method_names = ['get']
#
#     def get_queryset(self):
#         return self.queryset.filter(is_complete=True)
#
#     def list(self, request, *args, **kwargs):
#         paginator = StandardResultsSetPagination()
#         search_query = request.query_params.get('search', None)
#         if search_query:
#             if not SearchKeyword.objects.filter(keyword__iexact=search_query).exists():
#                 SearchKeyword.objects.create(keyword=search_query)
#
#             if  request.user.is_authenticated and not SearchKeyword.objects.filter(keyword__iexact=search_query, user=request.user.id).exists():
#                 SearchKeyword.objects.create(keyword=search_query, user=request.user)
#
#         queryset = self.filter_queryset(self.get_queryset())
#
#         if not search_query:
#             seed = request.query_params.get('seed', None)
#             if seed is None:
#                 seed = str(random.randint(0, 1e9))
#             seed_hash = int(sha256(seed.encode()).hexdigest(), 16) % (
#                         2 ** 31)
#
#             queryset = queryset.annotate(
#                 random_order=RandomOrder(F('id') * seed_hash, mod_value=100000)
#             ).order_by('random_order')
#
#         paginator = self.pagination_class()
#         page = paginator.paginate_queryset(queryset, request, view=self)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return paginator.get_paginated_response(serializer.data)
#
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)
#
# from django.contrib.postgres.search import SearchVector
# from django.db.models import F
# import random
# from hashlib import sha256
# from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
# from django.db.models import F
#
# class RetailProductListViewSet(ModelViewSet):
#     queryset = RetailProducts.objects.filter(disabled=False).prefetch_related('products_variations')
#     serializer_class = RetailProductListSerializer
#     filter_backends = [PrioritizedSearchFilter, DjangoFilterBackend]
#     search_fields = ['name', 'description', 'sub_category__category_name', 'category__department_name']
#     filterset_class = FilterForRetailProducts
#     pagination_class = RetailProductListPagination
#     http_method_names = ['get']
#
#     def get_queryset(self):
#         # Start with the base queryset for active and complete products
#         return self.queryset.filter(is_complete=True)
#
#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         search_query = request.query_params.get('search', None)
#
#         if search_query:
#             # Apply full-text search
#             queryset = self.apply_search(queryset, search_query)
#
#         # Apply filtering after search
#         queryset = self.filter_queryset(queryset)
#
#         # Paginate and serialize results
#         paginator = self.pagination_class()
#         page = paginator.paginate_queryset(queryset, request, view=self)
#         serializer = self.get_serializer(page if page is not None else queryset, many=True)
#         return paginator.get_paginated_response(serializer.data) if page else Response(serializer.data)
#
#     def apply_search(self, queryset, search_query):
#         """Applies full-text search using stemming and relevance ranking."""
#         search_query_object = SearchQuery(search_query, config='english')  # Use the 'english' configuration for stemming
#         search_vector = (
#             SearchVector('name', weight='A') +
#             SearchVector('description', weight='B') +
#             SearchVector('sub_category__category_name', weight='C') +
#             SearchVector('category__department_name', weight='D')
#         )
#
#         # Annotate relevance and filter by search query
#         return queryset.annotate(
#             search_rank=SearchRank(search_vector, search_query_object)
#         ).filter(
#             search_rank__gte=0.1  # Minimum rank threshold to filter out irrelevant results
#         ).order_by('-search_rank')
#
#     def log_search_query(self, search_query, request):
#         """Logs the search query for analytics and user behavior tracking."""
#         if not SearchKeyword.objects.filter(keyword__iexact=search_query).exists():
#             SearchKeyword.objects.create(keyword=search_query)
#         if request.user.is_authenticated and not SearchKeyword.objects.filter(
#                 keyword__iexact=search_query, user=request.user.id).exists():
#             SearchKeyword.objects.create(keyword=search_query, user=request.user)


from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from hashlib import sha256
import random

class RetailProductListViewSet(ModelViewSet):
    queryset = RetailProducts.objects.filter(disabled=False).prefetch_related('products_variations')
    serializer_class = RetailProductListSerializer
    filter_backends = [PrioritizedSearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'sub_category__category_name', 'category__department_name']
    filterset_class = FilterForRetailProducts
    pagination_class = RetailProductListPagination
    http_method_names = ['get']

    def get_queryset(self):
        # Start with the base queryset for active and complete products
        return self.queryset.filter(is_complete=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        search_query = request.query_params.get('search', None)

        if search_query:
            # Apply full-text search
            queryset = self.apply_search(queryset, search_query)
            # Log search query for analytics
            self.log_search_query(search_query, request)
        else:
            # Apply randomization if no search query
            queryset = self.apply_randomization(queryset, request)

        # Apply filtering after search or randomization
        queryset = self.filter_queryset(queryset)

        # Paginate and serialize results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        return paginator.get_paginated_response(serializer.data) if page else Response(serializer.data)

    def apply_search(self, queryset, search_query):
        """Applies full-text search using stemming and relevance ranking."""
        search_query_object = SearchQuery(search_query, config='english')  # Use the 'english' configuration for stemming
        search_vector = (
            SearchVector('name', weight='A') +
            SearchVector('description', weight='B') +
            SearchVector('sub_category__category_name', weight='C') +
            SearchVector('category__department_name', weight='D')
        )

        # Annotate relevance and filter by search query
        return queryset.annotate(
            search_rank=SearchRank(search_vector, search_query_object)
        ).filter(
            search_rank__gte=0.1  # Minimum rank threshold to filter out irrelevant results
        ).order_by('-search_rank')

    def apply_randomization(self, queryset, request):
        """Applies randomization to the queryset when there is no search query."""
        seed = request.query_params.get('seed', None)
        if seed is None:
            seed = str(random.randint(0, int(1e9)))
        seed_hash = int(sha256(seed.encode()).hexdigest(), 16) % (2 ** 31)

        # Randomize the order based on a hashed seed value
        return queryset.annotate(
            random_order=(F('id') * seed_hash) % 100000
        ).order_by('random_order')

    def log_search_query(self, search_query, request):
        """Logs the search query for analytics and user behavior tracking."""
        if not SearchKeyword.objects.filter(keyword__iexact=search_query).exists():
            SearchKeyword.objects.create(keyword=search_query)
        if request.user.is_authenticated and not SearchKeyword.objects.filter(
                keyword__iexact=search_query, user=request.user.id).exists():
            SearchKeyword.objects.create(keyword=search_query, user=request.user)


class NestedProductViewSet(ModelViewSet):
    queryset = RetailProducts.objects.filter(disabled=False)
    serializer_class = NestedProductSerializer
    permission_classes = [IsVendor]
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name', 'products_variations__sku']
    filterset_fields = ['is_complete']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.queryset.filter(vendor__user = self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.disabled = True
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

class RefundPolicyViewSet(ModelViewSet):
    queryset = RefundPolicy.objects.all()
    serializer_class = RefundPolicySerializer
    http_method_names = ['get']

class ProductRequestViewSet(ModelViewSet):
    queryset = ProductRequest.objects.all()
    serializer_class = ProductRequestSerializer
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request, message=None, code=None):
        if not request.user.is_authenticated:
            raise PermissionDenied(detail="You have to be signed in to use this feature.")
        return super().permission_denied(request, message, code)

#ADMIN
class AdminProductRequestViewSet(ModelViewSet):
    queryset = ProductRequest.objects.order_by('-created_date')
    serializer_class = ProductRequestSerializer
    http_method_names = ['get']
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

class AdminRetailVariationViewSet(ModelViewSet):
    queryset = RetailVariation.objects.filter(disabled=False)
    serializer_class = AdminRetailVariationSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name']
    filterset_fields = ['variation_type']
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

class AdminNestedProductViewSet(ModelViewSet):
    queryset = RetailProducts.objects.filter(disabled=False)
    serializer_class = AdminNestedProductSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name', 'products_variations__sku']
    filterset_fields = ['vendor']
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

class AdminRetailVariationTypeViewSet(ModelViewSet):
    queryset = RetailVariationType.objects.filter(disabled=False)
    serializer_class = AdminRetailVariationTypeSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

import csv
from rest_framework.response import Response
from io import TextIOWrapper
from django.db import transaction

#Upload product

class CSVProductUploadView(APIView):
    REQUIRED_FIELDS = [ 'sku','category', 'sub_category', 'product_name','product_description', 'price', 'stock',]

    def validate_row(self, row):
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not row.get(field, '').strip():
                errors.append(f"Missing or empty field: {field}")
        
        return errors
    
    def post(self, request):
        csv_file = request.FILES['file']
        vendor_id = request.data.get('vendor_id')

        if not csv_file.name.endswith('.csv'):
            return Response({'message': 'This is not a CSV file'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            raise ValidationError({"message": "Invalid vendor id."})

        try:
            raw_data = csv_file.file.read(10000)
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            csv_file.file.seek(0)

            # Read the CSV with detected encoding
            wrapped_file = TextIOWrapper(csv_file.file, encoding=encoding, errors='replace')
            reader = csv.DictReader(wrapped_file)
            
            with transaction.atomic():
                for row in reader:
                    # check empty row 
                    if not any(value.strip() for value in row.values()):
                        continue

                    errors = self.validate_row(row)
                    if errors:
                        return Response({"message":errors})
                    
                    if not any(row.values()):
                        continue

                    #department
                    if row.get('category'):
                        category_name = row['category'].strip().lower() 
                        category_data = VendorDepartment.objects.filter(department_name__iexact=category_name).first()
                        if not category_data:
                            category_data = VendorDepartment.objects.create(
                                department_name = row['category'].strip()
                            )
                        
                    #category
                    if row.get('sub_category'):
                        sub_category_name = row['sub_category'].strip().lower()
                        sub_category_data = VendorCategories.objects.filter(department=category_data, category_name__iexact=sub_category_name).first()
                        if not sub_category_data:
                            sub_category_data = VendorCategories.objects.create(
                                department = category_data,
                                category_name = row['sub_category'].strip()
                            )

                    #product
                    product_name = row['product_name'].strip().lower()
                    product_data = RetailProducts.objects.filter(name__iexact=product_name, category=category_data, sub_category=sub_category_data, vendor=vendor).first()
                    if not product_data:
                        product_data = RetailProducts.objects.create(
                            name = row['product_name'],
                            description = row['product_description'] if row['product_description'] else None,
                            category = category_data,
                            sub_category = sub_category_data,
                            vendor = vendor,
                            tax_rate = row['tax_rate'],
                            delivery_time = row['delivery_time'] if row['delivery_time'] else "same day delivery"
                        )
                    
                    #variation type/ variation
                    variation_instances = []
                            
                    if row['variation'] and row['variation_type']:
                        variations = row['variation'].split(",")
                        variation_types = row['variation_type'].split(",")


                        for variation, variation_type in zip(variations, variation_types):
                            variation = variation.lower()
                            variation_type = variation_type.lower()

                            variation_type_instance = RetailVariationType.objects.filter(name__iexact=variation_type).first()
                            if not variation_type_instance:
                                variation_type_instance = RetailVariationType.objects.create(name=variation_type)

                            variation_instance = RetailVariation.objects.filter(name__iexact=variation, variation_type=variation_type_instance).first()
                            if not variation_instance:
                                variation_instance = RetailVariation.objects.create(
                                    name=variation,
                                    variation_type=variation_type_instance
                                )

                            variation_instances.append(variation_instance)
                    

                    #product variation
                    sku = generate_sku(row['sku'], vendor_id)
                    product_variation = RetailProductsVariations.objects.filter(sku= sku, product__vendor=vendor).first()
                    if not product_variation:
                        product_variation = RetailProductsVariations.objects.create(
                            description = row['product_description'] if row['product_description'] else None,
                            product = product_data,
                            price = Decimal(row['price'].strip().replace(',', '')),
                            sku = sku,
                            stock_quantity = row['stock'],
                        )

                    if product_variation and  variation_instances:
                        product_variation.variation.set([variation_instance.id for variation_instance in variation_instances]) 
        except Exception as e:
            return Response({'message': f'An error occurred while processing the file.{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({'message': 'CSV file processed successfully'}, status=status.HTTP_201_CREATED)


class CSVProductExportView(APIView):
    def get(self, request):
        vendor_id = request.GET.get('vendor_id', None)
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            raise ValidationError({"message":"Invalid vendor id."})
        
        product_variations = RetailProductsVariations.objects.filter(product__vendor=vendor)

        filename = "Product.csv"
        fields = ['sku', 'category', 'sub_category', 'product_name', 'product_description', 'price', 'tax_rate', 'stock', 'variation_type', 'variation', 'default_image']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        writer = csv.writer(response)
        writer.writerow(fields)

        for product_variation in product_variations:
            variations = product_variation.variation.all()
            variations_name = ", ".join([variation.name for variation in variations])

            variation_types_name = ", ".join([variation.variation_type.name for variation in variations])

            writer.writerow([product_variation.sku, product_variation.product.category.department_name, product_variation.product.sub_category.category_name, product_variation.product.name, product_variation.product.description, product_variation.price, product_variation.product.tax_rate, product_variation.stock_quantity, variation_types_name, variations_name, product_variation.product.default_image])

        return response



class CategoryViewSet(ModelViewSet):
    queryset = VendorDepartment.objects.all()
    serializer_class = CategorySerializer 
    http_method_names = ['get']
    filter_backends = [SearchFilter]
    search_fields  = ['department_name', 'vendor']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = VendorDepartment.objects.filter(vendor_type = 2)
    
        limit = self.request.query_params.get('limit')
        vendor = self.request.query_params.get('vendor')
        department = self.request.query_params.get('department')

        if vendor:
            queryset = queryset.filter(vendor=vendor)
        
        if department:
            queryset = queryset.filter(department=department)

        if limit:
            try:
                limit = int(limit)
                if limit < 1:
                    raise ValidationError("'limit' must be a positive integer.")
            except ValueError:
                raise ValidationError("'limit' must be an integer.")
            
            queryset = queryset[:limit]

        return queryset


class SubCategoryViewSet(ModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = SubCategorySerializer
    http_method_names = ['get']
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['category_name', 'vendor']
    filterset_fields = ['vendor', 'department']

    def get_queryset(self):
        return VendorCategories.objects.filter(vendor_type = 2)

class ProductBulkDeleteView(ModelViewSet):
    queryset = RetailProducts.objects.all()
    serializer_class = RetailProductsSerializer
    http_method_names = ['delete']
    permission_classes = [IsVendor]

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        product_ids = request.data.get('ids', [])

        if not isinstance(product_ids, list):
            return Response({"message": "IDs should be provided in a list."})
        
        if not RetailProducts.objects.filter(id__in=product_ids, vendor=request.user.user):
            return Response({"message":"Invalid product"})
        
        products = RetailProducts.objects.filter(id__in=product_ids, vendor=request.user.user)

        if products:
            for product in products:
                product.disabled = True
                product.save()
        
        return Response({"message": f"{products.count()} products deleted successfully."},)


@api_view(['DELETE'])
@permission_classes([IsSuperAdmin])
def clear_cache(request):
    cache.clear()
    return Response({"message": "Cache cleared successfully"}, status=status.HTTP_200_OK)


class EditProductView(ModelViewSet):
    queryset = RetailProducts.objects.filter(disabled=False)
    serializer_class = EditProductSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields  = ['name']
    filterset_class = FilterForRetailProducts
    pagination_class = StandardResultsSetPagination
    # filterset_fields = ['category','sub_category','vendor',']
    http_method_names = ['get']


class VendorCategoryView(ModelViewSet):
    queryset = VendorDepartment.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['department_name']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return VendorDepartment.objects.filter(vendor_type=2, vendor__user=self.request.user).exclude(retail_products__isnull=True)
    
class VendorSubCategoryView(ModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['category_name']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return VendorCategories.objects.filter(vendor_type=2, vendor__user=self.request.user).exclude(retail_products__isnull=True)

# Price changes
class VendorPriceChange(APIView):
    def get(self, request, *args, **kwargs):
        vendor_id = request.query_params.get('vendor_id')
        times = request.query_params.get("times")

        try:
            vendor = Vendor.objects.get(id=vendor_id)
            product_variations = RetailProductsVariations.objects.filter(product__vendor=vendor.id)
            for variation in product_variations:
                variation.price = variation.price * Decimal(times)
                variation.save()
            return Response({"message":"Success"})
        except Vendor.DoesNotExist:
            return Response({"message":"Invalid vendor"})

# category changes
class CategoryChangeView(APIView):
    def get(self, request, *args, **kwargs):
        from_id = request.query_params.get('from')
        to_id = request.query_params.get('to')

        try:
            from_category = VendorDepartment.objects.get(id=from_id)
            to_category = VendorDepartment.objects.get(id=to_id)
        except VendorDepartment.DoesNotExist:
            return Response({'message':'Invalid category'})
        
        # check if sub-category exists 
        from_subcategory_names = set(from_category.vendor_categories.values_list('category_name', flat=True))
        to_subcategory_names = set(to_category.vendor_categories.values_list('category_name', flat=True))

        missing_subcategories = from_subcategory_names - to_subcategory_names

        if missing_subcategories:
            return Response({
                'message': f'Some subcategories of {from_category.department_name} do not exist in {to_category.department_name}',
                'missing_subcategories': list(missing_subcategories),
            }, status=400)
        
        with transaction.atomic():
            products = RetailProducts.objects.filter(category=from_category.id)
            if products:
                for product in products:
                    product.category = to_category
                    product.save()
                return Response({"message":"Success"})
            else:
                return Response({'message':f'Product doesnot exists in {from_category.department_name} category'})


@permission_classes([IsSuperAdmin])
class AddVendorDescriptionView(APIView):
    def post(self, request, *args, **kwargs):
        vendor_id = request.data.get('vendor', '')
        description = request.data.get('description', '')
        
        if not vendor_id and not description:
            return Response({'message': 'Vendor and description is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(id=vendor_id)
            retail_products = vendor.vendor_retails.all()
            for product in retail_products:
                product.description = product.description + " " + description
                product.save()
            
            return Response({'message':"Success"})
        except Vendor.DoesNotExist:
            raise ValidationError({'message':'Invalid vendor.'})