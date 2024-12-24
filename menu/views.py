from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework import viewsets, views

from rest_framework.exceptions import ValidationError
from datetime import datetime
import pytz
from rest_framework.permissions import AllowAny
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from timezonefinder import TimezoneFinder
from django.db.models import Q
from menu.models import CustomizationTitle, Customization, FoodAddonsFoodJunction, FoodItem, VendorCategories, VendorDepartment
from menu.serializers import AddFoodAddonsToFoodItemsSerializer, AddSecondaryCustomizationsSerializer, CustomizationSerializer, \
    CustomizationSerializer, CustomizationTitleSerializer, DiscountVendorCategoriesSerializer, EnableVendorCategorySerializer, FoodItemSerializer, FoodItemsSerializer, InputAddonsForVendorSerializer, InputFoodItemsForVendorSerializer, InputForFoodAddonsForVendorSerializer, \
    NestedCustomizationTitleSerializer, RemoveFoodAddonsToFoodItemsSerializer, RemoveSecondaryCustomizationsSerializer, UpdateOrderOfCategories, UpdateOrderOfCustomization, \
    VendorCategoriesSerializer, VendorDepartmentSerializer, ChangeOrderDepartmentOrderSerializer
from menu.user_categoty_serializer import UserSideVendorCategoriesSerializer
from rest_framework.decorators import action
from retail_orders.views import StandardResultsSetPagination
from utils.permissions_override import IsVendor

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from vendor.models import Vendor
from rest_framework import status
from rest_framework.filters import SearchFilter
# class CategoryViews(ModelViewSet):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer


class FoodItemViews(ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["vendor_categories", 'vendor','vendor__vendor_type']


class FoodAddonsCategoryViews(ModelViewSet):
    queryset = CustomizationTitle.objects.all()
    serializer_class = CustomizationTitleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['created_by__vendor_type']

    def get_queryset(self):
        vendor = Vendor.objects.filter(user = self.request.user).first()
        return CustomizationTitle.objects.filter(created_by = vendor)


class FoodAddonsViews(ModelViewSet):
    queryset = Customization.objects.all()
    serializer_class = CustomizationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["food_addons",'created_by__vendor_type']


# Nested view

class NestedFoodAddonsCategoryView(ModelViewSet):
    queryset = CustomizationTitle.objects.all()
    serializer_class = NestedCustomizationTitleSerializer
    permission_classes = [IsAuthenticated]


class CreateFoodItemsViewSet(ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemsSerializer
    # permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["vendor_categories", 'vendor','vendor__vendor_type']

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class VendorDepartmentViewSet(ModelViewSet):
    queryset = VendorDepartment.objects.all()
    serializer_class = VendorDepartmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['vendor__vendor_type']
    permission_classes = [IsAuthenticated]
    search_fields = ['department_name']
    pagination_class = StandardResultsSetPagination

    def get_local_time(self, latitude, longitude):
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        if timezone_str:
            timezone = pytz.timezone(timezone_str)
            local_time = datetime.now(timezone)
            return local_time
        else:
            return None

    def get_queryset(self):
        vendor = self.request.query_params.get("vendor", "")
        if not vendor:
            return VendorDepartment.objects.all()

        vendor = Vendor.objects.get(id=vendor)

        if not (vendor.vendor_location_latitude or vendor.vendor_location_longitude):
            return VendorDepartment.objects.filter(vendor=vendor)
        
        time_in_vendor = self.get_local_time(
            float(vendor.vendor_location_latitude), float(vendor.vendor_location_longitude))

        VendorDepartment.objects.select_related("hours_schedule").filter(
            Q(hours_schedule__starting_hours__lte=time_in_vendor,
            hours_schedule__ending_hours__gte=time_in_vendor,) |
            Q(hours_schedule = None)
        )

        return self.queryset.filter(
            Q(hours_schedule__starting_hours__lte=time_in_vendor,
            hours_schedule__ending_hours__gte=time_in_vendor,) |
            Q(hours_schedule = None),
            Q(vendor=vendor) | Q(vendor__isnull = True)
        )
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['department_order'] =  VendorDepartment.objects.all().count() + 1
        if request.user.role == 1:
            data['vendor'] = request.user.user.id
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "The department has been deleted successfully."},
            status=status.HTTP_200_OK
        )

class VendorCategoryViewSet(ModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = VendorCategoriesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["department", "vendor",'vendor__vendor_type']
    search_fields = ['category_name', 'department__department_name']
    pagination_class = StandardResultsSetPagination
   
    
    def get_queryset(self):
        if self.request.user.is_anonymous or self.request.user.role == 2:
            return VendorCategories.objects.all().filter(active=True).order_by("categories_order")
        else:
            return VendorCategories.objects.all()
            # user = self.request.user
            # return VendorCategories.objects.all().filter(vendor=self.request.user.user)
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['categories_order'] = VendorCategories.objects.all().count() + 1
        if request.user.role == 1:
            data['vendor'] = request.user.user.id
            data['active'] = False
        return super().create(request, *args, **kwargs)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "The category has been deleted successfully."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, url_path='disable_vendor_category', methods=['PATCH'])
    def disable_vendor_category(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return Response({"active":False},status=status.HTTP_200_OK)


class UserSideVendorCategoryViewSet(ReadOnlyModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = UserSideVendorCategoriesSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["department", "vendor",'vendor__vendor_type']


    def get_queryset(self):
        return VendorCategories.objects.all().filter(department__vendor__vendor_type=1).filter(active=True).order_by("categories_order")


class DiscountVendorCategoryViewSet(ModelViewSet):
    queryset = VendorCategories.objects.all()
    serializer_class = DiscountVendorCategoriesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["department", "vendor",'vendor__vendor_type']
    http_method_names = ['get']
    
    def get_queryset(self):
        if self.request.user.is_anonymous or self.request.user.role == 2:
            return VendorCategories.objects.order_by("categories_order").filter(active=True)
        else:
            user = self.request.user
            return VendorCategories.objects.order_by("categories_order").filter(vendor=self.request.user.user)


class EnableVendorCategoryView(ModelViewSet):
    permission_classes = [IsVendor]
    queryset = VendorCategories.objects.all().filter(active=False)
    serializer_class = EnableVendorCategorySerializer
    filter_backends = [DjangoFilterBackend]
    http_method_names = ['get','patch']
    filterset_fields = ["department", "vendor",'vendor__vendor_type']

    def get_queryset(self):
        request = self.request
        user = self.request.user
        return super().get_queryset().filter(vendor__user=self.request.user)

class AddFoodItemsForeVendorsViewSet(ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = InputFoodItemsForVendorSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        request = self.request
        user = request.user
        vendor = Vendor.objects.filter(user = user).first()
        return FoodItem.objects.filter(vendor = vendor).filter(vendor__vendor_type = 1)


class AddFoodAddOnsCategoryViewSet(ModelViewSet):
    queryset = CustomizationTitle.objects.all()
    serializer_class = InputAddonsForVendorSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        request = self.request
        user = request.user
        vendor = Vendor.objects.filter(user = user).first()
        return CustomizationTitle.objects.filter(created_by = vendor)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        data = request.data.copy()
        create_new_customization = []
        
        for each_data in data.get('customization_set', ""):

            if each_data.get("id",None):
                item = Customization.objects.get(id= each_data['id'])
                update_serializer = InputForFoodAddonsForVendorSerializer(item, each_data,many=False,partial=True,
                                                                           context={"request":self.request})
                update_serializer.is_valid(raise_exception=True)
                update_serializer.save()
            else:
                create_new_customization.append(each_data)
        
        request.data['customization_set'] = create_new_customization
        
        # serializer = InputAddonsForVendorSerializer(data=data, many=False, partial=True)
        # serializer.is_valid(raise_exception=True)
        request.data['customization_set'] = create_new_customization
        return super().partial_update(request, *args, **kwargs)


        return Response(serializer.data)



class AddAddonsToFoodItemsViewSet(ModelViewSet):
    queryset = FoodAddonsFoodJunction.objects.all()
    serializer_class  = AddFoodAddonsToFoodItemsSerializer
    permission_classes = [IsVendor]
    filter_backends =  [DjangoFilterBackend]
    filterset_fields = ['food_item','categories']
    http_method_names = ['put','get','post']

    # def get_queryset(self):
    #     request = self.request
    #     user = request.user
    #     vendor = Vendor.objects.get(user = user)
    #     return FoodAddonsFoodJunction.objects.filter()
    
#     {"items":[
# {
#         "food_item": 847,
#         "categories": 3
#    }]}
    
    def create(self, request, *args, **kwargs):
        data = request.data
        items = data.get('items',"")
        if not items:
            raise ValidationError({"message":"Data format wrong provided"})
        for each_item in items:
            food_addon = CustomizationTitle.objects.get(id=each_item['categories'])
            food_item = FoodItem.objects.get(id=each_item['food_item'])
            if not  FoodAddonsFoodJunction.objects.filter(food_item = food_item,
                                                          categories = food_addon).exists():
                try:
                    serializer=AddFoodAddonsToFoodItemsSerializer(data={"food_item":food_item.id, "categories":food_addon.id}, context={"request":request}, many=False)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                except Exception as e:
                    pass

        return HttpResponse(items, status = status.HTTP_200_OK)
    

class RemoveAddonsToFoodItemsViewSet(ModelViewSet):
    queryset = FoodAddonsFoodJunction.objects.all()
    serializer_class  = RemoveFoodAddonsToFoodItemsSerializer
    permission_classes = [IsVendor]
    http_method_names = ['delete','get','patch','put']


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        other_items = FoodAddonsFoodJunction.objects.filter(food_addons_order__gt = instance.food_addons_order)
        for other_item in other_items:
            other_item.food_addons_order = other_item.food_addons_order - 1
            other_item.save()
        return  super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        request = self.request
        user = request.user
        vendor = Vendor.objects.filter(user = user).first()
        return FoodAddonsFoodJunction.objects.filter(food_item__vendor = vendor)


class AddSecondaryCustomizationViewSet(ModelViewSet):
    queryset = Customization.objects.all()
    serializer_class = AddSecondaryCustomizationsSerializer
    permission_classes = [IsVendor]
    http_method_names = ['patch','get','post']

    # def get_queryset(self):
    #     request = self.request
    #     user = request.user
    #     vendor = Vendor.objects.get(user = user)
    #     return FoodAddons.objects.filter(created_by = vendor)


class RemoveSecondaryCustomizationViewSet(ModelViewSet):
    queryset = Customization.objects.all()
    serializer_class = RemoveSecondaryCustomizationsSerializer
    permission_classes = [IsVendor]
    http_method_names = ['patch','get']

    # def get_queryset(self):
    #     request = self.request
    #     user = request.user
    #     vendor = Vendor.objects.get(user = user)
    #     return FoodAddons.objects.filter(created_by = vendor)
    

class ChangeOrderingOfAddons(ModelViewSet):
    queryset = FoodAddonsFoodJunction.objects.all()
    serializer_class = UpdateOrderOfCategories
    permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['food_item','categories']

    def get_queryset(self):
        request = self.request
        user = request.user
        vendor = Vendor.objects.filter(user = user).first()
        return FoodAddonsFoodJunction.objects.filter(food_item__vendor = vendor)
    

class ChangeOrderFoodItemViewSet(ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = ChangeOrderDepartmentOrderSerializer
    permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor_categories','vendor__vendor_type']


    def get_queryset(self):
        return FoodItem.objects.filter(vendor__user = self.request.user).order_by("food_item_order")
    
class ChangeOrderCategoriesViewSet(views.APIView):
    def post(self, request, *args, **kwargs):
        category_order_data = request.data.get('category_order', [])
        if not category_order_data:
            return Response({"error": "No category order provided."}, status=status.HTTP_400_BAD_REQUEST)

        for category_data in category_order_data:
            category_order = category_data.get('category_order')
            category_id = category_data.get('category_id')
            
            if category_order is None or category_id is None:
                return Response({"error": "Invalid category data provided."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                categories = VendorCategories.objects.get(id=category_id)
                categories.categories_order = category_order
                categories.save()
            except VendorCategories.DoesNotExist:
                return Response({"error": f"Category with ID {category_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)
            
        serialized_data = VendorCategoriesSerializer(VendorCategories.objects.all(), many=True).data
        value = []
        for data in serialized_data:
            value.append({"category_id":data['id'], "category_order":data['categories_order']})

        return Response(value, status=status.HTTP_200_OK)

class ChangeOrderDepartmentsVIewSet(views.APIView):
    def post(self, request, *args, **kwargs):
        department_order_data = request.data.get('department_order', [])
        if not department_order_data:
            return Response({"error": "No category order provided."}, status=status.HTTP_400_BAD_REQUEST)

        for department_data in department_order_data:
            department_order = department_data.get('department_order')
            department_id = department_data.get('department_id')
            
            if department_order is None or department_id is None:
                return Response({"error": "Invalid department data provided."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                departments = VendorDepartment.objects.get(id=department_id)
                departments.department_order = department_order
                departments.save()
            except VendorDepartment.DoesNotExist:
                return Response({"error": f"Department with ID {department_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)
            
        serialized_data = VendorDepartmentSerializer(VendorDepartment.objects.all(), many=True).data
        value = []
        for data in serialized_data:
            value.append({"department_id":data['id'], "department_order":data['department_order']})

        return Response(value, status=status.HTTP_200_OK)
    

class ChangeOrderOfCustomizationViewSet(ModelViewSet):
    queryset = Customization.objects.all()
    serializer_class = UpdateOrderOfCustomization
    permission_classes = [IsVendor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customization_title','created_by__vendor_type']

    def get_queryset(self):
        return Customization.objects.filter(created_by__user = self.request.user).order_by("customization_order")
    


class RemoveFoodCustomization(ModelViewSet):
    queryset = Customization.objects.all()
    serializer_class  = CustomizationSerializer
    permission_classes = [IsVendor]
    http_method_names = ['delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customization_title']




    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        other_items = Customization.objects.filter(customization_order__gt = instance.customization_order,
                                                    customization_title = instance.customization_title)
        for other_item in other_items:
            other_item.customization_order = other_item.customization_order - 1
            other_item.save()
        return  super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        request = self.request
        user = request.user
        vendor = Vendor.objects.filter(user = user).first()
        return Customization.objects.filter(created_by = vendor)