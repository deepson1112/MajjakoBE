from uuid import uuid4
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.utils import timezone
from menu.serializers import CustomizationSerializer, FoodItemSerializer
from offers.models import LoyaltyPrograms
from orders.models import Order, OrderCustomization, OrderedFood, OrdersTaxDetails, Payment, PaymentInfo, VendorInvoices, VendorsOrders

class PaymentInfoSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = PaymentInfo

    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        return super().create(validated_data)


class PaymentsSerializers(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Payment

    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        return super().create(validated_data)

class OrderAddonsSerializer(ModelSerializer):
    customization = CustomizationSerializer(many=False, required=False)
    class Meta:
        fields = "__all__"
        model = OrderCustomization

    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        return super().create(validated_data)


class OrderedFoodSerializer(ModelSerializer):
    food_item = FoodItemSerializer(many=False, required=False)
    
    class Meta:
        fields = "__all__"
        model = OrderedFood

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['food_item']['order_food_addons'] =  OrderAddonsSerializer(OrderCustomization.objects.filter(food=instance), many=True).data
        return data

    
    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        return super().create(validated_data)


class VendorOrdersSerializer(ModelSerializer):
    ordered_food = OrderedFoodSerializer(many=True)
    class Meta:
        fields ="__all__"
        model = VendorsOrders

class DisplayLoyaltySerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = LoyaltyPrograms
class OrdersSerializer(ModelSerializer):
    order_vendor = VendorOrdersSerializer(many=True, required=False)
    loyalty_program = DisplayLoyaltySerializer(many=False, required=False)
    
    class Meta:
        fields = "__all__"
        model = Order





class VendorInvoicesSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = VendorInvoices

    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['ordered_food_details'] = [
            OrderedFoodSerializer(OrderedFood.objects.get(id=each_order), many=False).data
         for each_order in data['ordered_food']]
        return data


class OrdersTaxDetailsSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = OrdersTaxDetails

    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        return super().create(validated_data)



##########################
    

