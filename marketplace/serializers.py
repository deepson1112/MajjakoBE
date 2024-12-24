from datetime import datetime, timedelta
import decimal
import uuid
from rest_framework.serializers import ModelSerializer
from timezonefinder import TimezoneFinder
import pytz
from marketplace.models import Cart, FoodCustomizations
from rest_framework import serializers
from marketplace.utils import ProductDetailsService
from menu.models import Customization, FoodItem
from offers.models import Coupons, FreeDelivery, GetOneFreeOffer, LoyaltyPrograms, SaveOnItemsDiscountPercentage, SaveOnItemsOffer, StoreOffer
from django.db.models import Q
from django.utils import timezone
from user.models import User, UserProfile

from vendor.models import Vendor

class CartAddonsSerializer(ModelSerializer):
    active = serializers.BooleanField(required=False, default=True, write_only=True)
    
    class Meta:
        fields = "__all__"
        model = FoodCustomizations
        read_only_fields = ['cart','created_at','updated_at']

    def create(self, validated_data):
        active = validated_data.pop('active')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        active = validated_data.pop('active')

        if active == False:
            customization = FoodCustomizations.objects.filter(id = instance.id)
            customization.delete()    
            return FoodCustomizations.objects.none() 
        
        return super().update(instance, validated_data)



    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['customization_set'] = {"id":instance.customization.id, "title":instance.customization.title,'price':instance.customization.price}
        return data


class CartSerializer(ModelSerializer):
    cart_addons = CartAddonsSerializer(many=True, required=False)
    class Meta:
        exclude = ['active']
        model = Cart
        read_only_fields = ['user','created_at','updated_at','quantity','cart_id']

    def to_representation(self, instance):
        data =  super().to_representation(instance)
        food_item =  FoodItem.objects.get(id=instance.fooditem.id)
        data['fooditem'] = {
            "id" : instance.fooditem.id,
            "name" :instance.fooditem.food_title,
            "vendor" : instance.fooditem.vendor.vendor_name
        }

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        cart_addons = validated_data.pop("cart_addons", "")
        validated_data['cart_id'] = uuid.uuid4()
        cart = Cart.objects.create(**validated_data)
        for cart_addon in cart_addons:
            FoodCustomizations.objects.create(
                cart = cart,
                customization =cart_addon['customization'],
                quantity = cart_addon['quantity']
            )
        return cart
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        cart_addons = validated_data.pop("cart_addons", "")
        for cart_addon in cart_addons:
            FoodCustomizations.objects.create(
                cart = instance,
                customization =cart_addon['customization'],
                quantity = cart_addon['quantity']

            )
            
        return super().update(instance, validated_data)
    
class UpdateCartItemsItems(serializers.Serializer):
    quantity = serializers.IntegerField(required=True)
    id = serializers.IntegerField(read_only=True)

    def update(self, instance, validated_data):
        instance.quantity = validated_data['quantity']
        instance.save()
        return instance
    

class UpdateQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Cart
        read_only_fields = ['user','fooditem',"created_at",'updated_at','special_request','receiver_name','active']

class CartItemsQuantitySerializer(serializers.Serializer):
    fooditem = serializers.PrimaryKeyRelatedField(queryset = Cart.objects.all())
    quantity = serializers.IntegerField() 

    def to_representation(self, instance):
        data =  super().to_representation(instance)
        request = self.context.get("request")
        data['total_quantity'] = Cart.objects.filter(user=request.user, active=True).filter(fooditem= instance.fooditem).count()
        return data

class SaveOnItemsDiscountPercentageForCart(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = SaveOnItemsDiscountPercentage

class SaveOnItemsOfferForCart(serializers.ModelSerializer):
    offer_items = serializers.SerializerMethodField() 

    offer_type = serializers.SerializerMethodField()
    
    def get_offer_type(self, instance):
        return "SAVE ON ITEMS"
    
    def get_offer_items(self, instance):
        return SaveOnItemsDiscountPercentageForCart(SaveOnItemsDiscountPercentage.objects.get(id = self.context.get("id")), 
                                                    many=False, context = {"request":self.context.get("request")}).data
    
    class Meta:
        fields = ["offer_type", "audience",'start_date','end_date','id','offer_items']
        model = SaveOnItemsOffer

class GetOneFreeOfferForCartSerializer(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()

    def get_offer_type(self, instance):
        return "GET ONE FREE"
    
    class Meta:
        fields = "__all__"
        model = GetOneFreeOffer

class StoreOfferForCartSerializer(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()
    def get_offer_type(self, instance):
        return "STORE OFFER"
    class Meta:
        fields = "__all__"
        model = StoreOffer

class FoodItemDetailSerializer(serializers.ModelSerializer):
    customer_type = serializers.SerializerMethodField(read_only=True)
    discount = serializers.SerializerMethodField()
    tax_percentage = serializers.SerializerMethodField()
    class Meta:
        fields = ["id",'food_title','discount','customer_type','price','tax_percentage','image']
        model = FoodItem

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
                                               context = {"request":self.context.get("request"), "id":specific_discount.store_offer.id} , 
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
                                               context = {"request":self.context.get("request"), "id":specific_discount.store_offer.id} , 
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

class UserCartsBreakdownSerializer(serializers.ModelSerializer):
    fooditem = FoodItemDetailSerializer(many=False, required=True)
    free_delivery = serializers.SerializerMethodField()
    cart_addons = CartAddonsSerializer(many=True, required=False)

    class Meta:
        fields = "__all__"
        model = Cart

    def get_free_delivery(self, instance):
        current_time = timezone.now()
        delivery = FreeDelivery.objects.filter(
            Q(start_date__lte  = current_time , end_date__gte = current_time)
        )
        return delivery.values()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        customization_cost = data['cart_addons']
        addons_cost = 0
        for each_item in customization_cost:
            addons_cost += each_item['customization_set']['price'] * each_item['quantity']
        
        data['per_item_addon_cost'] = addons_cost
        addons_cost = addons_cost * data['quantity']

        tax_amount = (instance.fooditem.price * instance.quantity) * (decimal.Decimal(instance.fooditem.vendor.tax_rate) /100)
        data['tax_amount'] = tax_amount
        try:
            if data['fooditem']['discount']['offer_type'] == "SAVE ON ITEMS":
                data['fooditem']['discount']['offer_items'] = SaveOnItemsDiscountPercentage.objects.filter(store_offer__id = data['fooditem']['discount']['id']).values()
                data['discount_percentage'] =  data['fooditem']['discount']['offer_items'][0]['discount_percentages']
                data['addons_cost'] = addons_cost
                
                data['discount_amount'] = (instance.fooditem.price * instance.quantity) * (decimal.Decimal(data['discount_percentage'] / 100)) 
                data['discounted_amount'] =  (instance.fooditem.price * instance.quantity) - data['discount_amount'] 
                data['per_item_amount'] = instance.fooditem.price
                data['actual_amount'] = instance.fooditem.price * instance.quantity

            if data['fooditem']['discount']['offer_type'] == "GET ONE FREE":
                data['fooditem']['discount']['offer_items'] = [{"id":instance.fooditem.id,
                                                        "food_title":instance.fooditem.food_title
                                                        }]
                data['discount_percentage'] =  0
                data['addons_cost'] = addons_cost
                
                data['discount_amount'] = 0
                data['discounted_amount'] =  0
                data['per_item_amount'] = instance.fooditem.price
                data['actual_amount'] = 0
            if data['fooditem']['discount']['offer_type'] == "STORE OFFER":
                data['fooditem']['discount']['offer_items'] =[ {"id":instance.fooditem.id,
                                                        "food_title":instance.fooditem.food_title
                                                        }]
                data['discount_percentage'] = data['fooditem']['discount']['discount_percentages']
                data['addons_cost'] = addons_cost


                data['actual_amount'] = instance.fooditem.price * instance.quantity
                data['per_item_amount'] = instance.fooditem.price
                data['discount_amount'] = 0
                data['discounted_amount'] = 0

                if data['actual_amount'] >  data['fooditem']['discount']['minimum_spend_amount']:
                    discounted_amount = data['actual_amount'] * decimal.Decimal(data['discount_percentage'] / 100 )
                    data['discount_amount'] = discounted_amount
                    data['discounted_amount'] = data['actual_amount']  - decimal.Decimal(discounted_amount)
                


                # data['discount_amount'] = data['actual_amount'] - (data['fooditem']['discount']['maximum_redeem_value'] * instance.quantity) if data['actual_amount'] > (data['fooditem']['discount']['minimum_spend_amount'] * instance.quantity) else 0
                # data['discounted_amount'] =  data['actual_amount'] - data['discount_amount']
                
        except Exception as e:
            data['discount_percentage'] = 0
            data['addons_cost'] = addons_cost
            data['actual_amount'] = instance.fooditem.price * instance.quantity
            data['per_item_amount'] = instance.fooditem.price
            data['discount_amount'] = 0
            data['discounted_amount'] =  data['actual_amount']
            return data
        return data
    
class VendorCouponsDescriptionForCart(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Coupons



    

class DiscountVendorSerializer(ModelSerializer):
    food_items = serializers.SerializerMethodField()
    coupons_offer = serializers.CharField(allow_null=True, required=False)
    calculate_coupons = serializers.SerializerMethodField()
    delivery_time = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        fields =["id","food_items","coupons_offer","calculate_coupons","delivery_time", "vendor_name","vendor_slug","tax_exempt","tax_rate","vendor_logo","vendor_cover_image"]
        model = Vendor

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['discount_amount'] = sum(items['discount_amount'] for items in data['food_items'])
        data['discounted_price'] = sum(items['discounted_amount'] for items in data['food_items'])
        data['total_tax'] = sum(items['tax_amount'] for items in data['food_items'])
        data['addons_cost'] = sum(items['addons_cost'] for items in data['food_items'])

        data['sub_total'] = decimal.Decimal(data['discounted_price']) + decimal.Decimal(data['addons_cost']) + (data['total_tax'])

        data['amount_after_coupon_discount'] = data['sub_total'] - data['calculate_coupons']

        data["total_amount"] = data['amount_after_coupon_discount']

        return data
    
    def get_local_time(self, latitude, longitude):
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        if timezone_str:
            timezone = pytz.timezone(timezone_str)
            local_time = datetime.now(timezone)
            return local_time
        else:
            return None


    def get_calculate_coupons(self, instance):
        coupon_code = instance.coupons_offer
        # print(coupon_code)
        if not (coupon_code == "" or coupon_code == None):
        
            code_value = Coupons.objects.get(coupon_code = coupon_code)
            return decimal.Decimal(code_value.discount_amount)
        return 0
        return decimal.Decimal(code_value.discount_amount) if (coupon_code != "" or coupon_code != None) else 0


    def get_food_items(self, instance):
        current_time = timezone.now()
        weekday = current_time.weekday()
        request = self.context.get('request')
        user = request.user
        user_cart = Cart.objects.filter(user=user, active=True).filter(fooditem__vendor = instance)

        # if instance.delivery_time:
        #     delivery_time = instance.delivery_time
        #     delivery_time_plus_4 = current_time + timedelta(hours=4)
        #     if delivery_time_plus_4.time() < delivery_time.time():
        #         cart = Cart.objects.filter(user=request.user).filter(active=True).filter(fooditem__vendor = instance).filter(
        #             Q(fooditem__hours_schedule__starting_hours__gte = current_time, fooditem__hours_schedule__ending_hours__lte = current_time) | 
        #             Q(fooditem__hours_schedule = None)
        #         ).filter(
        #             Q(fooditem__vendor_categories__hours_schedule__starting_hours__gte = current_time, fooditem__vendor_categories__hours_schedule__ending_hours__lte = current_time) | 
        #             Q(fooditem__vendor_categories__hours_schedule = None)
        #         )
        #         return UserCartsBreakdownSerializer(user_cart, many=True, context={"request":request}).data

        for each_item in user_cart:

            delivery_time = instance.delivery_time

            delivery_time_plus_4 = current_time + timedelta(hours=4)
            if delivery_time_plus_4.time() < delivery_time.time():
                time_in_vendor = self.get_local_time(float(each_item.fooditem.vendor.vendor_location_latitude) , float(each_item.fooditem.vendor.vendor_location_longitude))
                food_item = each_item.fooditem
                if food_item.hours_schedule:
                    if time_in_vendor.time() > food_item.hours_schedule.starting_hours and time_in_vendor.time() < food_item.hours_schedule.ending_hours and weekday in food_item.hours_schedule.week_days:
                        continue
                    else:
                        user_cart = user_cart.exclude(id=each_item.id)
                elif food_item.vendor_categories.hours_schedule:
                    if time_in_vendor > food_item.vendor_categories.hours_schedule.starting_hours and time_in_vendor < food_item.vendor_categories.hours_schedule.ending_hours and weekday in food_item.vendor_categories.hours_schedule.week_days:
                        continue
                    else:
                        user_cart = user_cart.exclude(id=each_item.id)
                elif food_item.vendor_categories.department.hours_schedule:
                    if time_in_vendor > food_item.vendor_categories.department.hours_schedule.starting_hours and time_in_vendor < food_item.vendor_categories.department.hours_schedule.ending_hours and weekday in food_item.vendor_categories.department.hours_schedule.week_days:
                        continue
                    else:
                        user_cart = user_cart.exclude(id=each_item.id)
                else:
                    continue
        
        return UserCartsBreakdownSerializer(user_cart, many=True, context={"request":request}).data
    


class CartCalculationsSerializer(serializers.Serializer):
    cart = UserCartsBreakdownSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        sub_total = sum(item.get('discounted_amount', 0) for item in data['cart']) 
        actual_amount = sum(item.get('actual_amount', 0) for item in data['cart']) 
        for each_item in data['cart']:
            for item in each_item['cart_addons']:
                sub_total += decimal.Decimal(item['customization_set']['price'] ) * item['quantity']
                actual_amount += decimal.Decimal(item['customization_set']['price'] ) * item['quantity']

        total_tax = sum(item.get('tax_amount', 0) for item in data['cart']) 

        data['total_tax'] = total_tax
        data['sub_total'] = sub_total
        data['actual_amount'] = actual_amount
        data['grand_total'] = data['total_tax'] + data['sub_total'] 
        return data
    

class GetVendorsSerializer(serializers.Serializer):
    vendors = DiscountVendorSerializer(many=True)
    tip = serializers.SerializerMethodField(read_only=True, allow_null=True)
    loyalty_code = serializers.SerializerMethodField()

    def get_tip(self, instance):
        request = self.context.get("request")
        tip = request.query_params.get("tip","0")
        if not tip:
            return float("0")
        return float(tip)
    
    def get_loyalty_code(self,instance):
        request = self.context.get("request")
        code = request.GET.get("loyalty_code", "")
        if code == "":
            return ""
        else:
            user = request.user
            user_coupons = UserProfile.objects.get(id=user.user.id)
            coupon_details = LoyaltyPrograms.objects.get(program_code = code)
            if user_coupons.loyalty_points < coupon_details.no_of_points:
                raise serializers.ValidationError({"message":"The user does not have enough points to redeem this coupon"})
            else:
                return coupon_details.program_code
            
            
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['discount_amount'] = sum(items['discount_amount'] for items in data['vendors'])
        data['discounted_price'] = sum(items['discounted_price'] for items in data['vendors'])
        data['total_tax'] = sum(items['total_tax'] for items in data['vendors'])
        data['addons_cost'] = sum(items['addons_cost'] for items in data['vendors'])

        data['sub_total'] = decimal.Decimal(data['discounted_price']) + decimal.Decimal(data['addons_cost']) + (data['total_tax'])


        data["total_amount"] = sum(item['amount_after_coupon_discount'] for item in data['vendors']) + decimal.Decimal(data['tip'])

        if self.get_loyalty_code(instance):
            loyalty = LoyaltyPrograms.objects.get(
                program_code = self.get_loyalty_code(instance))
            
            
            if (loyalty.minimum_spend_amount) > data['total_amount']:
                raise serializers.ValidationError({"message":"The minimum spend amount for loyalty is not fulfilled"})
            
            data['loyalty_type'] = "Amount"  if LoyaltyPrograms.objects.get(
                program_code = self.get_loyalty_code(instance)).discount_percentages == 0.0 else "Discount"
    
            data['loyalty_discount'] = loyalty.discount_percentages if data['loyalty_type'] == "Discount" else loyalty.maximum_redeem_amount
            data["total_amount"] = data["total_amount"] - decimal.Decimal(data["total_amount"] * decimal.Decimal(data['loyalty_discount']/100)) if data['loyalty_type'] == "Discount" else  data["total_amount"] - decimal.Decimal(loyalty.maximum_redeem_amount)
        else:
            data['loyalty_type'] = ""
            data['loyalty_discount'] = ""

        return data

