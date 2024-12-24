from rest_framework.request import Request
from django.utils import timezone
from django.db.models import Q
from menu.models import FoodItem
from offers.models import GetOneFreeOffer, SaveOnItemsDiscountPercentage, SaveOnItemsOffer, StoreOffer
from rest_framework import serializers



class StoreOfferForCartService(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    def get_discount_percentage(self, instance):
        return 0
    
    def get_offer_type(self, instance):
        return "STORE OFFER"
    
    class Meta:
        fields = "__all__"
        model = StoreOffer

class GetOneFreeOfferService(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()

    def get_offer_type(self, instance):
        return "GET ONE FREE"
    
    class Meta:
        fields = "__all__"
        model = GetOneFreeOffer

class SaveOnItemsOfferService(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()
    
    class Meta:
        fields = ["offer_type", "audience",'start_date','end_date','id']
        model = SaveOnItemsOffer

    def get_offer_type(self, instance):
        return "SAVE ON ITEMS"

class SaveOnItemsService(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()
    
    class Meta:
        fields = ["offer_type", "audience",'start_date','end_date','id']
        model = SaveOnItemsOffer

    def get_offer_type(self, instance):
        return "SAVE ON ITEMS"
class ProductDetailsService:
    """
        This class provides the client with all the details of the product required to 
        place order
    """
    def __init__(self, instance,delivery_time=None, request:Request= Request ,query = None ) -> None:
        self.request = request
        self.query = query
        self.current_time = timezone.now()
        self.instance = instance
        self.delivery_time = delivery_time

    def create_date_query(self, query, date):
        self.current_time = timezone.now()
        return query.filter(
            Q(start_date__lte=self.current_time, end_date__gte=self.current_time)
        )

    def get_discount_on_items(self, instance):
        food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(item = instance).filter(
                Q(store_offer__start_date__lte=self.current_time, store_offer__end_date__gte=self.current_time)
                )
            
        if food_item_discount:
            specific_discount = SaveOnItemsDiscountPercentage.objects.filter(item = instance).get(
                Q(store_offer__start_date__lte=self.current_time, store_offer__end_date__gte=self.current_time)
            
                )
            data = SaveOnItemsService(SaveOnItemsOffer.objects.get(id = specific_discount.store_offer.id), many=False).data
            return data

        food_item_discount = SaveOnItemsDiscountPercentage.objects.filter(category = instance.vendor_categories).filter(
                Q(store_offer__start_date__lte=self.current_time, store_offer__end_date__gte=self.current_time)
                )
        if food_item_discount:
            specific_discount = SaveOnItemsDiscountPercentage.objects.filter(category = instance.vendor_categories).get(
                    Q(store_offer__start_date__lte=self.current_time, store_offer__end_date__gte=self.current_time))
            return SaveOnItemsOfferService(SaveOnItemsOffer.objects.get(id = specific_discount.store_offer.id), many=False).data

    def get_one_for_free(self, instance):
        offer = GetOneFreeOffer.objects.filter(item = instance.id).filter(
                    ( Q(start_date__lte=self.current_time, end_date__gte=self.current_time))
                )
        if offer:
            actual_discount = GetOneFreeOffer.objects.filter(item = instance.id).get(
                Q(start_date__lte=self.current_time, end_date__gte=self.current_time))
            
            return GetOneFreeOfferService(actual_discount, many=False).data

    def get_store_offer(self, instance):
        store_offer = StoreOffer.objects.filter(
                        Q(start_date__lte=self.current_time, end_date__gte=self.current_time)
                        )
        if store_offer:
            actual_offer = StoreOffer.objects.get(
            Q(start_date__lte=self.current_time, end_date__gte=self.current_time)
            )
            return StoreOfferForCartService(actual_offer, many=False).data

    def get_discount(self, instance, delivery_time=None):
        if self.get_discount_on_items(instance):
            return self.get_discount_on_items(instance)
        elif self.get_one_for_free(instance):
            return self.get_one_for_free(instance)
        elif self.get_store_offer(instance):
            return self.get_store_offer(instance)
        else:
            return 



