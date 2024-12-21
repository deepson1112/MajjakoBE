from django.utils import timezone
from rest_framework.serializers import ModelSerializer
from marketplace.models import Cart
from marketplace.serializers import FoodItemDetailSerializer, GetOneFreeOfferForCartSerializer, SaveOnItemsOfferForCart, StoreOfferForCartSerializer
from menu.models import CustomizationTitle, Customization, FoodAddonsFoodJunction, FoodItem, VendorCategories, VendorDepartment
from offers.models import GetOneFreeOffer, SaveOnItemsDiscountPercentage, SaveOnItemsOffer, StoreOffer
from vendor.models import Vendor
from rest_framework import serializers
from django.db.models import Q

from django.db import transaction
from django.db.models import F, Max

# class CategorySerializer(ModelSerializer):
#     class Meta:
#         fields = "__all__"
#         model = Category
#         read_only_fields = ["slug"]


class FoodItemSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FoodItem


class CustomizationSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Customization
        read_only_fields = ['categories']


class CustomizationTitleSerializer(ModelSerializer):
    food_addons = CustomizationSerializer(many=True)

    class Meta:
        fields = "__all__"
        model = CustomizationTitle

    def create(self, validated_data):
        food_addons_data = validated_data.pop('food_addons')
        addons_instance = CustomizationTitle.objects.create(**validated_data)
        for addon in food_addons_data:
            Customization.objects.create(food_addons=addons_instance, **addon)
        return addons_instance


# This is the sample code for the nested serializer

class NestedCustomizationSerializer(ModelSerializer):

    class Meta:
        fields = "__all__"
        model = Customization
        read_only_fields = ['customization_title']


class NestedCustomizationTitleSerializer(ModelSerializer):
    customization_set = NestedCustomizationSerializer(many=True, write_only=False)

    class Meta:
        fields = "__all__"
        model = CustomizationTitle
        reqd_only_fields = ['created_by']

    def create(self, validated_data):
        foodaddons = validated_data.pop('customization_set', None)
        request = self.context.get('request')
        user = request.user
        created_by = Vendor.objects.get(user=user.id)
        validated_data['created_by'] = created_by
        addons_category = CustomizationTitle.objects.create(**validated_data)

        for addons in foodaddons:
            Customization.objects.create(food_addons=addons_category, **addons)
        return addons_category


# The nested serializer Category

class CustomizationSerializer(ModelSerializer):
    old_id = serializers.IntegerField(write_only=True, required=False)
    class Meta:
        fields = "__all__"
        model = Customization
        # read_only_fields = ['food_addons']


class CustomizationTitleSerializer(ModelSerializer):
    old_id = serializers.IntegerField(write_only=True, required=False)
    class Meta:
        fields = "__all__"
        model = CustomizationTitle
        read_only_fields = ["food_item", "created_by"]


class FoodItemsSerializer(ModelSerializer):
    # CustomizationTitle_set = CustomizationTitleSerializer(
    #     many=True, allow_null=True, required=False)
    
    food_addons = serializers.SerializerMethodField(read_only=True)

 

    def get_food_addons(self, instance):
        addon_categories = CustomizationTitle.objects.filter(food_addons__food_item = instance.id).order_by('-food_addons__food_addons_order')
        return InputAddonsForVendorSerializer(addon_categories, many=True).data

    class Meta:
        fields = "__all__"
        model = FoodItem
        read_only_fields = ["slug", "created_at", "updated_at", "vendor"]

    def update(self, instance, validated_data):
        food_addons_categories = validated_data.pop(
            "CustomizationTitle_set", "")

        if food_addons_categories:
            for food_addons_category in food_addons_categories:
                food_addons = food_addons_category.pop("customization_set", "")

                if food_addons_category.get("old_id", None):
                    created_food_addons_category = CustomizationTitle.objects.get(
                        id=food_addons_category.pop("old_id"))
                    created_food_addons = CustomizationTitleSerializer(
                        created_food_addons_category, food_addons_category, many=False)
                else:
                    created_food_addons_category = CustomizationTitle.objects.create(
                        food_item=instance, **food_addons_category)

                if food_addons:
                    for food_addon in food_addons:
                        if food_addon.get("old_id", None):
                            created_food_addon = Customization.objects.get(
                                id=food_addon.pop("old_id"))
                            CustomizationSerializer(
                                created_food_addon, food_addon, many=False)
                        else:
                            Customization.objects.create(
                                food_addons=created_food_addons_category, **food_addon)

        return super().update(instance, validated_data)

    def create(self, validated_data):
        request = self.context.get("request")
        food_addons_categories = validated_data.pop(
            "CustomizationTitle_set", "")
        
        validated_data['vendor'] = request.user.user

        food_item = super().create(validated_data)

        if food_addons_categories:
            for food_addons_category in food_addons_categories:
                food_addons = food_addons_category.pop("customization_set", "")
                created_food_addons = CustomizationTitle.objects.create(
                    food_item=food_item, **food_addons_category)

                if food_addons:
                    for food_addon in food_addons:
                        Customization.objects.create(
                            food_addons=created_food_addons, **food_addon)

        return food_item


class VendorCategoriesSerializer(ModelSerializer):
    fooditem_set = FoodItemsSerializer(many=True, read_only=True)

    class Meta:
        fields = "__all__"
        model = VendorCategories
        read_only_fields = ["category_slug",'active']
    

class EnableVendorCategorySerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = VendorCategories
        read_only_fields = ["category_slug",'department','category_name','category_slug','category_description','vendor','tax_rate','tax_exempt','age_restriction','hours_schedule','active']

    def update(self, instance, validated_data):
        instance.active = True
        instance.save()
        return instance

class VendorDepartmentSerializer(ModelSerializer):
    vendorcategories_set = VendorCategoriesSerializer(
        many=True, read_only=True)

    class Meta:
        fields = "__all__"
        model = VendorDepartment
        read_only_fields = ["department_slug"]


# Individual based food addons for the vendor Views
class SecCustomizationForAddonsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Customization


    
class SecCustomizationCustomizationTitleSerializer(serializers.ModelSerializer):
    customization_set = SecCustomizationForAddonsSerializer(many=True, read_only=True)
    class Meta:
        fields = "__all__"
        model = CustomizationTitle
        


class InputForFoodAddonsForVendorSerializer(serializers.ModelSerializer):
    # old_id = serializers.IntegerField(write_only=True, required=False)
    # customization = SecCustomizationCustomizationTitleSerializer(read_only=True)

    class Meta:
        fields = "__all__"
        model = Customization
        read_only_fields = ['customization_title']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['customization'] = SecCustomizationCustomizationTitleSerializer(instance.customization, many=False).data if instance.customization else None
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context.get('request').user.user
        # validated_data['customization_order'] = Customization.objects.filter(customization_title=validated_data['customization_title']).count() + 1

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['created_by'] = self.context.get('request').user.user
        validated_data['customization_order'] = Customization.objects.filter(customization_title=instance.customization_title).count() + 1

        return super().update(instance, validated_data)


class InputAddonsForVendorSerializer(serializers.ModelSerializer):
    customization_set = InputForFoodAddonsForVendorSerializer(
        many=True, allow_null=False, required=False)
    class Meta:
        fields = "__all__"
        model = CustomizationTitle
        read_only_fields = ['food_item', 'created_by']

    def update(self, instance, validated_data):
        food_addons = validated_data.pop("customization_set", "")
        for food_addon in food_addons:
            Customization.objects.create(**food_addon, customization_title=instance,
                                         created_by = self.context.get('request').user.user,
                                          customization_order = Customization.objects.filter(customization_title=instance).count() + 1
                                         )
        return super().update(instance, validated_data)

    def create(self, validated_data):
        food_addons_data = validated_data.pop('customization_set', "")
        request = self.context.get('request')
        user = request.user
        vendor = Vendor.objects.get(user=user)
        validated_data['created_by'] = vendor
        addons_instance = CustomizationTitle.objects.create(**validated_data)
        for addon in food_addons_data:
            Customization.objects.create(customization_title=addons_instance,
                                          created_by = self.context.get('request').user.user
                                          ,**addon,
                                          customization_order = Customization.objects.filter(customization_title=addons_instance).count() + 1
                                          )
        return addons_instance
    

class InputFoodAddonsId(serializers.ModelSerializer):
    class Meta:
        fields = ["id"]
        model = CustomizationTitle

class InputFoodItemsForVendorSerializer(serializers.ModelSerializer):
    food_addons = serializers.SerializerMethodField(read_only=True)
    customization_titles = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True) 

    class Meta:
        fields = "__all__"
        model = FoodItem
        read_only_fields = ['vendor','slug']

    def get_food_addons(self, instance):
        addon_categories = CustomizationTitle.objects.filter(food_addons__food_item = instance.id).order_by('food_addons__food_addons_order')
        return InputAddonsForVendorSerializer(addon_categories, many=True).data

    def validate(self, attrs):
        user = self.context.get('request').user
        vendor = Vendor.objects.get(user= user)
        hours_schedule = attrs.get('hours_schedule',"")
        vendor_categories = attrs.get('vendor_categories', "")

        if vendor_categories:
            if vendor_categories.vendor != vendor:
                raise serializers.ValidationError({"msg":"The Vendor Category does not belong to the logged in vendor" }) 
        if hours_schedule:
            if hours_schedule.vendor != vendor:
                raise serializers.ValidationError({"msg":"The hours scheduled does not belong to the logged in vendor" }) 
        
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        vendor = Vendor.objects.get(user=user)
        validated_data['vendor'] = vendor

        customization_titles = validated_data.pop("customization_titles", "")
        if customization_titles:
            food = super().create(validated_data)
            order = 1    
            for customization_title in customization_titles:
                try:
                    item = CustomizationTitle.objects.get(id=customization_title, created_by=request.user.user)
                except:
                    raise serializers.ValidationError({"msg":"The customization does not exist or belong to the logged in user"})
                FoodAddonsFoodJunction.objects.create(
                    food_item = food,
                    categories = item,
                    food_addons_order = order 
                )
                order += 1 
            return food
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")

        customization_titles = validated_data.pop("customization_titles", "")
        
        if customization_titles:
            FoodAddonsFoodJunction.objects.filter(
                food_item = instance,
            ).exclude(categories__in = customization_titles).delete()

            for customization_title in customization_titles:
                try:
                    item = CustomizationTitle.objects.get(id=customization_title, created_by=request.user.user)
                except:
                    raise serializers.ValidationError({"msg":"The customization does not exist or belong to the logged in user"})
                order =  FoodAddonsFoodJunction.objects.filter(food_item = instance, categories = item).count() + 1
                FoodAddonsFoodJunction.objects.get_or_create(
                    food_item = instance,
                    categories = item,
                    defaults={'food_addons_order': order}
                )

        return super().update(instance, validated_data)


class AddFoodAddonsToFoodItemsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FoodAddonsFoodJunction
        read_only_fields = ['food_addons_order']
    
    #TOdo 
    def create(self, validated_data):
        vendor = self.context.get('request').user.user
        add_on_category = validated_data['categories']
        food_item_id = validated_data['food_item']
       
        count = FoodAddonsFoodJunction.objects.filter(food_item = food_item_id).count()
        validated_data['food_addons_order'] = count + 1
        
        if food_item_id.vendor != vendor:
            raise serializers.ValidationError({"msg":"the food item does not belong to logged in user"})

        if add_on_category.created_by != vendor:
            raise serializers.ValidationError({"msg":"the addons does not belong to logged in user"})
        
        return FoodAddonsFoodJunction.objects.create(**validated_data)
        

class RemoveFoodAddonsToFoodItemsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FoodAddonsFoodJunction

    # def update(self, instance, validated_data):
    #     vendor = self.context.get('request').user.user
    #     if instance.created_by != vendor:
    #         raise serializers.ValidationError({"msg":"the addons does not belong to logged in user"})
    #     try:
    #         food_item = FoodItem.objects.get(id=validated_data['food_item_id'])
    #     except FoodItem.DoesNotExist:
    #         raise serializers.ValidationError({"msg":"The food items does not exist"})
    #     instance.food_item.remove(food_item)
    #     instance.save()
    #     return instance
        

class AddSecondaryCustomizationsSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = "__all__"
        model = Customization
        read_only_fields = ['food_addons', 'title', 'price' , 'maximum_number' , 'description','image','multiple_orders','secondary_customization','created_by','customization_title']

    def update(self, instance, validated_data):

        if instance.customization_title == validated_data['customization']:
            raise serializers.ValidationError({"msg":"Same item cannot be added its secondary customization"})
        
        instance.customization = validated_data['customization']
        instance.secondary_customization = True
        instance.save()
        return instance
    
class RemoveSecondaryCustomizationsSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = "__all__"
        model = Customization
        read_only_fields = ['food_addons', 'title', 'price' , 'maximum_number' , 'description','image','multiple_orders','secondary_customization','created_by']

    def update(self, instance, validated_data):
        instance.customization = None
        instance.secondary_customization = False
        instance.save()
        return instance
    

class UpdateOrderOfCategories(serializers.ModelSerializer):
    customization_title = serializers.CharField(source='categories.add_on_category', read_only=True)
    food_title = serializers.CharField(source='food_item.food_title', read_only=True)

    class Meta:
        model = FoodAddonsFoodJunction
        fields = ['id', 'food_addons_order', 'food_item', 'categories', 'customization_title', 'food_title']
        read_only_fields = ["categories", "food_item", "customization_title", "food_title"]

    def update(self, instance, validated_data):
        new_order = validated_data.get('food_addons_order')
        current_order = instance.food_addons_order


        if current_order < new_order:
            old_orders = FoodAddonsFoodJunction.objects.filter(categories__id = instance.categories.id
                                                  ).filter(food_addons_order__gte = current_order , food_addons_order__lte = new_order)
            
            for old_order in old_orders:
                old_order.food_addons_order = old_order.food_addons_order - 1
                old_order.save()

        elif current_order > new_order:
            old_orders = FoodAddonsFoodJunction.objects.filter(categories__id = instance.categories.id
                                                  ).filter(food_addons_order__gte = new_order, food_addons_order__lte = current_order)
            
            for old_order in old_orders:
                old_order.food_addons_order = old_order.food_addons_order + 1
                old_order.save()
        else:
            pass
        
        instance.food_addons_order = new_order
        instance.save()
        return instance
    

class UpdateOrderOfCustomization(serializers.ModelSerializer):

    class Meta:
        model = Customization
        fields = "__all__"
        read_only_fields = ["customization_title", "title", "price", "maximum_number","description",
                            "image","created_by","multiple_selection","secondary_customization","customization"
                            ]

    def update(self, instance, validated_data):
        new_order = validated_data.get('customization_order')

        current_order = instance.customization_order


        if current_order < new_order:
            old_orders = Customization.objects.filter(customization_title__id = instance.customization_title.id
                                                  ).filter(customization_order__gte = current_order , customization_order__lte = new_order)
            
            for old_order in old_orders:
                old_order.customization_order = old_order.customization_order - 1
                old_order.save()

        elif current_order > new_order:
            old_orders = Customization.objects.filter(customization_title__id = instance.customization_title.id
                                                  ).filter(customization_order__gte = new_order, customization_order__lte = current_order)
            
            for old_order in old_orders:
                old_order.customization_order = old_order.customization_order + 1
                old_order.save()
        else:
            pass
        
        instance.customization_order = new_order
        instance.save()
        return instance
    

#######################


class FoodAddonsFoodJunctionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FoodAddonsFoodJunction

class VendorFoodItemDetailsSerializer(serializers.ModelSerializer):
    customer_type = serializers.SerializerMethodField(read_only=True)
    discount = serializers.SerializerMethodField()
    tax_percentage = serializers.SerializerMethodField()
    food_addons = serializers.SerializerMethodField(read_only=True)
    discount_amount = serializers.SerializerMethodField(allow_null=True)
    discounted_amount = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        fields = "__all__"
        model = FoodItem

    def get_discounted_amount(self, instance):
        discount = self.get_discount_amount(instance)
        return float(instance.price) - discount

    def get_discount_amount(self, instance):
        discount = self.get_discount(instance)

        if discount:
            if discount['offer_type'] == "SAVE ON ITEMS":
                return float(instance.price)  / discount["offer_items"]["discount_percentages"]
        return 0

    

    def get_food_addons(self, instance):
        return FoodAddonsFoodJunctionSerializer(FoodAddonsFoodJunction.objects.filter(food_item=instance), many=True).data

    def get_tax_percentage(self, instance):
        vendor_tax_percentage = instance.vendor.tax_rate
        return vendor_tax_percentage
    
    def get_customer_type(self, instance):
        request = self.context.get("request")
        # if not request.user.orders:
        #     return "NEW CUSTOMER"
        # if request.user.orders:
        #     return "All Customer"
        # else:
        #     return "All Active Customer"
        return "ALL CUSTOMER"
    
    # def get_discount(self, instance):
    #     discount = ProductDetailsService(
    #         instance=instance, request=self.context.get('request'))
    #     return discount.get_discount(instance)
    
    def get_discount(self, instance):
        customer_type = self.get_customer_type
        current_time = timezone.now()
        try:
            food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(item = instance).filter(
                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                )
            
            
            if food_item_discount:
                specific_discount = SaveOnItemsDiscountPercentage.objects.filter(item = instance).get(
                    Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                
                    )
                data = SaveOnItemsOfferForCart(SaveOnItemsOffer.objects.get(id = specific_discount.store_offer.id),
                                               context = {"request":self.context.get("request"), "id":specific_discount.id}, 
                                               many=False).data
                return data
            else:
                raise SaveOnItemsDiscountPercentage.DoesNotExist
        except SaveOnItemsDiscountPercentage.DoesNotExist:
            food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(category = instance.vendor_categories).filter(
                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                )
            if food_item_discount:
                specific_discount = SaveOnItemsDiscountPercentage.objects.filter(category = instance.vendor_categories).get(
                        Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time))
                
                return SaveOnItemsOfferForCart(SaveOnItemsOffer.objects.get(id = specific_discount.store_offer.id),
                                               context = {"request":self.context.get("request"), "id":specific_discount.id}, 
                                               many=False).data
            else:
                offer = GetOneFreeOffer.objects.filter(item = instance.id).filter(
                    ( Q(start_date__lte=current_time, end_date__gte=current_time))
                )
                if offer:
                    actual_discount = GetOneFreeOffer.objects.filter(item = instance.id).get(
                        Q(start_date__lte=current_time, end_date__gte=current_time))
                    
                    return GetOneFreeOfferForCartSerializer(actual_discount, many=False).data
                else:
                    store_offer = StoreOffer.objects.filter(
                        Q(start_date__lte=current_time, end_date__gte=current_time)
                        )
                    if store_offer:
                        actual_offer = StoreOffer.objects.get(
                        Q(start_date__lte=current_time, end_date__gte=current_time)
                        )
                        return StoreOfferForCartSerializer(actual_offer, many=False).data
        return None



class DiscountVendorCategoriesSerializer(ModelSerializer):
    fooditem_set = serializers.SerializerMethodField(read_only=True) 
    

    class Meta:
        fields = "__all__"
        model = VendorCategories
        read_only_fields = ["category_slug",'active','vendor']

    def get_fooditem_set(self, instance):

        return VendorFoodItemDetailsSerializer(FoodItem.objects.filter(vendor_categories=instance).order_by("food_item_order"), many=True, context={"request":self.context.get('request')}).data

class ChangeOrderDepartmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["food_item_order","vendor_categories","food_title","id"]
        model = FoodItem
        read_only_fields = ['vendor_categories','food_title']

    def update(self, instance, validated_data):
        new_order = validated_data.get('food_item_order')
        current_order = instance.food_item_order

        if current_order < new_order:
            old_orders = FoodItem.objects.filter(vendor_categories__id = instance.vendor_categories.id
                                                  ).filter(food_item_order__gte = current_order , food_item_order__lte = new_order)

            for old_order in old_orders:
                old_order.food_item_order = old_order.food_item_order - 1
                old_order.save()

        elif current_order > new_order:
            old_orders = FoodItem.objects.filter(vendor_categories__id = instance.vendor_categories.id
                                                  ).filter(food_item_order__gte = new_order, food_item_order__lte = current_order)
            
            for old_order in old_orders:
                old_order.food_item_order = old_order.food_item_order + 1
                old_order.save()
        else:
            pass
        
        instance.food_item_order = new_order
        
        instance.save()

        return instance