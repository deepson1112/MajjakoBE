from django.utils import timezone
from rest_framework.serializers import ModelSerializer
from marketplace.serializers import GetOneFreeOfferForCartSerializer, SaveOnItemsDiscountPercentageForCart, SaveOnItemsOfferForCart, StoreOfferForCartSerializer
from offers.models import FreeDelivery, GetOneFreeOffer, SaveOnItemsDiscountPercentage, SaveOnItemsOffer, StoreOffer
from rest_framework import serializers
from vendor.models import FAQS, Offerings, OpeningHour, Vendor, VendorHourTimelines
from django.db.models import Q

class OfferingsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Offerings

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["vendor_set"] = instance.vendor_set.all().values("id","vendor_name","is_approved","vendor_phone")
        return data

class FreeDeliveryForVendorSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FreeDelivery


class SaveOnItemsOfferForVendor(serializers.ModelSerializer):
    offer_items = serializers.SerializerMethodField() 

    offer_type = serializers.SerializerMethodField()
    
    def get_offer_type(self, instance):
        return "SAVE ON ITEMS"
    
    def get_offer_items(self, instance):
        return SaveOnItemsDiscountPercentageForCart(SaveOnItemsDiscountPercentage.objects.filter(store_offer = instance), 
                                                    many=True, context = {"request":self.context.get("request")}).data
    
    class Meta:
        fields = ["offer_type", "audience",'start_date','end_date','id','offer_items']
        model = SaveOnItemsOffer

class VendorSerializer(ModelSerializer):
    free_delivery = serializers.SerializerMethodField()
    customer_type = serializers.SerializerMethodField()
    get_one_for_free = serializers.SerializerMethodField()
    store_offer = serializers.SerializerMethodField()
    save_on_items = serializers.SerializerMethodField()
    vendor_type_display = serializers.ReadOnlyField(source = 'get_vendor_type_display', allow_null=True)

    class Meta:
        model = Vendor
        fields = "__all__"

    def get_customer_type(self, instance):
        request = self.context.get("request")
        return "ALL CUSTOMER"
    
    def get_save_on_items(self, instance):
        current_time = timezone.now()

        discount  = SaveOnItemsOffer.objects.filter(vendor = instance).filter(
                Q(start_date__lte=current_time, end_date__gte=current_time))
        return SaveOnItemsOfferForVendor(discount, many=True, context = {"request":self.context.get('request')}).data
    

    def get_store_offer(self, instance):
        current_time = timezone.now()
        actual_offer = StoreOffer.objects.filter(Q(start_date__lte=current_time, end_date__gte=current_time))
        return StoreOfferForCartSerializer(actual_offer, many=True).data
    

    def get_get_one_for_free(self, instance):
        current_time = timezone.now()
        actual_discount = actual_discount = GetOneFreeOffer.objects.filter(vendor=instance).filter(
            Q(start_date__lte=current_time, end_date__gte=current_time))
        return GetOneFreeOfferForCartSerializer(actual_discount, many=True).data


    def get_discount(self, instance):
        customer_type = self.get_customer_type
        current_time = timezone.now()
        try:
            food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(store_offer__vendor = instance).filter(
                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                )
                        
            if food_item_discount:
                specific_discount = food_item_discount.first()
                data = SaveOnItemsOfferForCart(specific_discount.store_offer, many=False).data
                
                return data
            else:
                raise SaveOnItemsDiscountPercentage.DoesNotExist
        except SaveOnItemsDiscountPercentage.DoesNotExist:
            food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(store_offer__vendor = instance.vendor_categories).filter(
                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                )
            if food_item_discount:
                specific_discount = food_item_discount.first()
                return SaveOnItemsOfferForCart(specific_discount.store_offer, many=False).data
            else:
                offer = GetOneFreeOffer.objects.filter(vendor = instance.id).filter(
                    ( Q(start_date__lte=current_time, end_date__gte=current_time))
                )
                if offer:
                    actual_discount = offer.first()
                    
                    return GetOneFreeOfferForCartSerializer(actual_discount, many=False).data
                else:

                    store_offer = StoreOffer.objects.filter(
                        Q(start_date__lte=current_time, end_date__gte=current_time)
                        )
                    if store_offer:
                        actual_offer = store_offer.first()
                        return StoreOfferForCartSerializer(actual_offer, many=False).data
        return None

    def get_free_delivery(self, instance):
        current_time = timezone.now()
        return FreeDeliveryForVendorSerializer(FreeDelivery.objects.filter(
            Q(start_date__lte=current_time, end_date__gte=current_time)
        ),
        many=True
        ).data

class OpeningHourSerializer(ModelSerializer):
    class Meta:
        model = OpeningHour
        fields = "__all__"


class VendorHoursSerializer(ModelSerializer):
    class Meta:
        model = VendorHourTimelines
        fields = "__all__"
        read_only_fields = ['vendor']

    def create(self, validated_data):
        validated_data['vendor'] = self.context.get("request").user.user
        return super().create(validated_data)


class FAQSSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FAQS