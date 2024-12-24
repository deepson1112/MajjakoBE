from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from menu.models import FoodItem, VendorCategories
from offers.models import Coupons, GetOneFreeOffer, LoyaltyPrograms, SaveOnItemsOffer, StoreOffer, SaveOnItemsDiscountPercentage
from django.db.models import Q
from user.models import UserProfile
from django.utils import timezone
class StoreOfferSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model= StoreOffer
        read_only_fields = ['vendor','created_by','created_date','active']

    def validate(self, attrs):
        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")
        if not discount_start_date and discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})
        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"the discount start date is smaller than discount start date"})
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['vendor'] = request.user.user
        discount_start_date = validated_data.get('start_date',"")
        discount_end_date = validated_data.get('end_date',"")
        discounts = StoreOffer.objects.filter(
            Q(start_date__range=(discount_start_date, discount_end_date)) | 
            Q(end_date__range=(discount_start_date, discount_end_date)) |
            Q(start_date__lte=discount_start_date, end_date__gte=discount_end_date)
            )
        if discounts.exists():
            raise serializers.ValidationError({"message":f"Store offer already exists for the selected date"})
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        discount_start_date = validated_data.get('start_date',"")
        discount_end_date = validated_data.get('end_date',"")
        discounts = StoreOffer.objects.exclude(id = instance.id).filter(
            Q(start_date__range=(discount_start_date, discount_end_date)) | 
            Q(end_date__range=(discount_start_date, discount_end_date)) |
            Q(start_date__lte=discount_start_date, end_date__gte=discount_end_date)
            )
        if discounts.exists():
            raise serializers.ValidationError({"message":f"Store's offer already exists for the selected date"})
        return super().update(instance, validated_data)        


class GetOneFreeOfferSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model= GetOneFreeOffer
        read_only_fields = ['vendor','created_by','created_date','active']

    def validate(self, attrs):
        request = self.context.get("request")
        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")
        offer_items = attrs.get("item","")
        if not discount_start_date and discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})

        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"the discount start date is smaller than discount start date"})

        
        return super().validate(attrs)

    def to_representation(self, instance):
        data =  super().to_representation(instance)
        data['item'] = [{"item_name":FoodItem.objects.get(id=item).food_title, "item_id":FoodItem.objects.get(id=item).id} for item in data['item']]
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        discount_start_date = validated_data.get('start_date',"")
        discount_end_date = validated_data.get('end_date',"")
        offer_items = validated_data.get("item","")


        for each_item in offer_items:     
            if each_item.vendor != request.user.user:
                raise serializers.ValidationError({"msg":"food item does not belong to the vendor"})
            
            food_item = GetOneFreeOffer.objects.filter(item=each_item).filter(
                Q(start_date__range=(discount_start_date, discount_end_date)) | 
                Q(end_date__range=(discount_start_date, discount_end_date)) |
                Q(start_date__lte=discount_start_date, end_date__gte=discount_end_date)
                )
            if food_item.exists():
                raise serializers.ValidationError({"message":f"item food{each_item} already has a offer existing"})

        validated_data['created_by'] = request.user
        validated_data['vendor'] = request.user.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')

        discount_start_date = validated_data.get('start_date',"")
        discount_end_date = validated_data.get('end_date',"")
        offer_items = validated_data.get("item","")


        for each_item in offer_items:     
            if each_item.vendor != request.user.user:
                raise serializers.ValidationError({"msg":"food item does not belong to the vendor"})
            
            food_item = GetOneFreeOffer.objects.filter(item=each_item).filter(
                Q(start_date__range=(discount_start_date, discount_end_date)) | 
                Q(end_date__range=(discount_start_date, discount_end_date)) |
                Q(start_date__lte=discount_start_date, end_date__gte=discount_end_date)
                ).exclude(id=instance.id)
            if food_item.exists():
                raise serializers.ValidationError({"message":f"item food{each_item} already has a offer existing"})

        validated_data['created_by'] = request.user
        validated_data['vendor'] = request.user.user
        return super().update(instance, validated_data)


class SaveOnItemsDiscountPercentageSerializer(serializers.ModelSerializer):
    discount_on =  serializers.SerializerMethodField(read_only = True)

    def get_discount_on(self, instance):
        return "item" if instance.item != None else "category"
    class Meta:
        fields = ['id', 'discount_percentages', 'item', 'category','store_offer',"discount_on"]

        model = SaveOnItemsDiscountPercentage
        read_only_fields = ['store_offer']


class SaveOnItemsOfferSerializer(serializers.ModelSerializer):
    offer_items = SaveOnItemsDiscountPercentageSerializer(many=True, allow_null=True, required=False)

    class Meta:
        fields = "__all__"
        model = SaveOnItemsOffer
        read_only_fields = ['vendor','created_by','created_date','active']

    def validate(self, attrs):
        offer_items = attrs.get('offer_items',[])
        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")
        if not discount_start_date and discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})
        request = self.context.get("request")

        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"the discount start date is smaller than discount start date"})

        for each_item in offer_items:
            item = each_item.get('item',None)
            category = each_item.get('category',None)
            old_id = each_item.get('old_id',None)

            if item and category:
                raise serializers.ValidationError({"msg":"both food item and category cannot be selected"})
            
            if item:
                if item.vendor != request.user.user:
                    raise serializers.ValidationError({"msg":"food item does not belong to the vendor"})
                food_item = SaveOnItemsDiscountPercentage.objects.filter(item=item).filter(
                    Q(store_offer__start_date__range=(discount_start_date, discount_end_date)) | 
                    Q(store_offer__end_date__range=(discount_start_date, discount_end_date)) |
                    Q(store_offer__start_date__lte=discount_start_date, store_offer__end_date__gte=discount_end_date)
                    ).exclude(id=old_id)
            
            if category:
                if category.vendor!= request.user.user:
                    raise serializers.ValidationError({"msg":"food item deos not belong to the vendor"})
                food_item = SaveOnItemsDiscountPercentage.objects.filter(category=category).filter(
                    Q(store_offer__start_date__range=(discount_start_date, discount_end_date)) | 
                    Q(store_offer__end_date__range=(discount_start_date, discount_end_date)) |
                    Q(store_offer__start_date__lte=discount_start_date, store_offer__end_date__gte=discount_end_date)
                    ).exclude(id=old_id)
            
            if food_item.exists():
                raise serializers.ValidationError({"message":f"item food{item} already has a offer existing"})

        return super().validate(attrs)

    
    def create(self, validated_data):
        request = self.context.get('request')
        offer_items = validated_data.pop('offer_items',[])
        
        validated_data['created_by'] = request.user
        validated_data['vendor'] = request.user.user
        
        
        
        instance =  SaveOnItemsOffer.objects.create(**validated_data)
        for each_items in offer_items:
            SaveOnItemsDiscountPercentage.objects.create(**each_items, store_offer = instance)
        return instance


    def update(self, instance, validated_data):
        offer_items = validated_data.pop('offer_items',"")
        for each_item in offer_items:
            if each_item.get("old_id",None):
                offer_item = SaveOnItemsDiscountPercentage.objects.get(id=each_item.pop('old_id'))

                test = SaveOnItemsDiscountPercentageSerializer(offer_item, each_item, partial=True)
                
                if test.is_valid(raise_exception=True):
                    test.save()
            else:
                SaveOnItemsDiscountPercentage.objects.create(**each_item, store_offer = instance)
      
      
        request = self.context.get('request')
        user = request.user
        
        validated_data['created_by'] = request.user
        validated_data['vendor'] = request.user.user

        return super().update(instance, validated_data)
    
    

class DisableStoreOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["active"]
        model = StoreOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.active = False
        instance.save()
        return instance


class DisableGetOneFreeOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["active"]
        model = GetOneFreeOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.active = False
        instance.save()
        return instance
    

class DisableSaveOnItemsOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["active"]
        model = SaveOnItemsOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.active = False
        instance.save()
        return instance



class ViewAvailableCouponsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Coupons
        read_only_fields = ['vendor','created_date','updated_date']
    
    def create(self, validated_data):
        request = self.context.get('request')
        current_time = timezone.now()

        validated_data['vendor'] = request.user.user
        validated_data['created_date'] = current_time
        validated_data['updated_date'] = current_time

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        current_time = timezone.now()

        validated_data['updated_date'] = current_time

        return super().update(instance, validated_data)

class LoyaltyProgramsSerializer(serializers.ModelSerializer):
    valid = serializers.SerializerMethodField()
    class Meta:
        model = LoyaltyPrograms
        fields = '__all__'

    def get_valid(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        try:
            user_profile = UserProfile.objects.get(user=user)
            return user_profile.loyalty_points >= obj.no_of_points
        except UserProfile.DoesNotExist:
            return False
