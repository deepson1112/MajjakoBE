from django.utils import timezone
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from menu.models import Customization, CustomizationTitle, FoodItem, VendorCategories
from menu.serializers import CustomizationSerializer, CustomizationTitleSerializer, InputAddonsForVendorSerializer
from offers.models import SaveOnItemsDiscountPercentage
from django.db.models import Q

    


class UserSideFoodItemSerializer(ModelSerializer):
    food_addons = serializers.SerializerMethodField(read_only=True)
    discount_amount = serializers.SerializerMethodField()
    discounted_amount = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
 
    def get_food_addons(self, instance):
        addon_categories = CustomizationTitle.objects.filter(food_addons__food_item = instance.id).order_by('food_addons__food_addons_order')
        return InputAddonsForVendorSerializer(addon_categories, many=True).data

    def get_discount_percentage(self, instance):
        current_time = timezone.now()

        try:
            food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(item = instance).filter(
                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                )
            
            
            if food_item_discount:
                specific_discount = SaveOnItemsDiscountPercentage.objects.filter(item = instance).get(
                    Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                
                    )
                
                return specific_discount.discount_percentages
            else:
                raise SaveOnItemsDiscountPercentage.DoesNotExist
        except SaveOnItemsDiscountPercentage.DoesNotExist:
            food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(category = instance.vendor_categories).filter(
                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                )
            if food_item_discount:
                specific_discount = SaveOnItemsDiscountPercentage.objects.filter(category = instance.vendor_categories).get(
                        Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time))
                
                return specific_discount.discount_percentages
        return 0

    def get_discount_amount(self, instance):
        discount_percentages = self.get_discount_percentage(instance)
        if discount_percentages != 0:
            return float(instance.price) * (discount_percentages/100)
        return 0


    def get_discounted_amount(self, instance):
        discount_amount = self.get_discount_amount(instance)
        if discount_amount:
            return float(instance.price) - discount_amount
        return instance.price

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
    

class UserSideVendorCategoriesSerializer(ModelSerializer):
    fooditem_set = UserSideFoodItemSerializer(many=True, read_only=True)

    class Meta:
        fields = "__all__"
        model = VendorCategories
        read_only_fields = ["category_slug",'active','vendor']

