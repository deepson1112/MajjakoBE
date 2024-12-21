import uuid
from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q

from .models import RetailCart, RetailDeliveryCharge
from retail.models import ProductsVariationsImage, RetailProducts, RetailProductsVariations, RetailVariation
from retail_offers.models import PlatformOffer, RetailGetOneFreeOffer, RetailSaveOnItemsOffer, RetailSaveOnItemsDiscountPercentage, RetailStoreOffer, VendorPlatformOffer

class DisplayRetailProductsImage(serializers.ModelSerializer):
    class Meta:
        fields = ["default_image", "image_1", "image_2", "image_3", "image_4"]
        model = RetailProducts

class RetailCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailCart
        fields = "__all__"
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        shared_wishlist = validated_data.pop('shared_wishlist', None)
        buy_now = validated_data.get('buy_now', False)
        special_request = validated_data.get('special_request', None)

        if shared_wishlist  == None and buy_now == False and special_request == None:
            if RetailCart.objects.filter(retail_product_variation = request.data['retail_product_variation'], user=request.user, active=True, shared_wishlist=None, buy_now=False, special_request=None).exists():
                cart = RetailCart.objects.filter(retail_product_variation = request.data['retail_product_variation'], user=request.user, active=True, shared_wishlist=None, buy_now=False, special_request=None).first()
                cart.quantity += request.data['quantity']
                cart.save()
                return cart
        
        if shared_wishlist != None:
            validated_data['shared_wishlist'] = shared_wishlist
            validated_data['receiver_name'] = request.user.first_name + " " + request.user.last_name

        if buy_now:
            cart_instance = RetailCart.objects.filter(active=True, buy_now=True).exists()
            if cart_instance:
                cart_instance = RetailCart.objects.filter(active=True, buy_now=True).first()
                cart_instance.buy_now = False
                cart_instance.active = False
                cart_instance.save()
                
        validated_data['user'] = request.user
        validated_data['cart_id'] = uuid.uuid4()
        cart = RetailCart.objects.create(**validated_data)

        return cart
    
    def update(self, instance, validated_data):
        quantity = validated_data.get('quantity', '')
        if quantity:
            if quantity > instance.retail_product_variation.stock_quantity:
                raise serializers.ValidationError({
                    'message': f"Quantity ({quantity}) cannot exceed available stock ({ instance.retail_product_variation.stock_quantity})."
                })

        return super().update(instance, validated_data)

class RetailSaveOnItemsDiscountPercentageForCart(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = RetailSaveOnItemsDiscountPercentage

class RetailSaveOnItemsOfferForCartSerializer(serializers.ModelSerializer):
    discount_percentages = serializers.SerializerMethodField()
    offer_type = serializers.SerializerMethodField()
    
    def get_offer_type(self, instance):
        return "SAVE ON ITEMS"
    
    def get_offer_items(self, instance):
        return RetailSaveOnItemsDiscountPercentageForCart(RetailSaveOnItemsDiscountPercentage.objects.get(id = self.context.get("id")), 
                                                    many=False, context = {"request":self.context.get("request")}).data
    
    def get_discount_percentages(self, instance):
        offer = self.get_offer_items(instance)
        return offer['discount_percentages']
    
    class Meta:
        fields = ['id', "offer_type", "audience",'start_date','end_date', 'discount_percentages']
        model = RetailSaveOnItemsOffer
        
        


class RetailGetOneFreeOfferForCartSerializer(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()

    def get_offer_type(self, instance):
        return "GET ONE FREE"
    
    class Meta:
        fields = "__all__"
        model = RetailGetOneFreeOffer

class RetailStoreOfferForCartSerializer(serializers.ModelSerializer):
    offer_type = serializers.SerializerMethodField()

    def get_offer_type(self, instance):
        return "STORE OFFER"
    
    class Meta:
        fields = "__all__"
        model = RetailStoreOffer

class VendorPlatformOfferForCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPlatformOffer
        fields = "__all__"

class PlatformOfferForCartSerializer(serializers.ModelSerializer):
    discount_percentages = serializers.SerializerMethodField()
    offer_type = serializers.SerializerMethodField()

    def get_offer_type(self, instance):
        return "PLATFORM OFFER"
    
    def get_offer_item(self, instance):
        return VendorPlatformOfferForCartSerializer(VendorPlatformOffer.objects.get(id = self.context.get("id","")), 
                                                     context = {"request":self.context.get("request")}).data
    
    def get_discount_percentages(self, instance):
        offer = self.get_offer_item(instance)
        return offer['discount_percentages']
    
    class Meta:
        fields = ['id', "offer_type", "audience",'start_date','end_date', 'discount_percentages']
        model = PlatformOffer

class DisplayProductsVariationsImageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ProductsVariationsImage
        read_only_fields = ['variation','created_date']

def calculate_discount(discount, actual_price):
    discount_type = discount['offer_type']
    discount_amount = 0
    discounted_amount = 0

    if discount_type == "SAVE ON ITEMS":
        discount_percentage = discount["discount_percentages"]
        discount_amount = float(discount_percentage/100) * float(actual_price)

    if discount_type == "STORE OFFER":
        discount_percentage = discount["discount_percentages"]
        discount_amount = float(discount_percentage/100) * float(actual_price)
    
    if discount_type == "PLATFORM OFFER":
        discount_percentage = discount["discount_percentages"]
        discount_amount = float(discount_percentage/100) * float(actual_price)

    if discount_amount:
        discounted_amount = float(actual_price) - discount_amount

    return (discount_amount, discounted_amount)

class DetailProductsVariationsImageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ProductsVariationsImage
        read_only_fields = ['variations','created_date']

class RetailProductsVariationsDetailSerializer(serializers.ModelSerializer):
    customer_type = serializers.SerializerMethodField()
    tax_percentage = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    tax_exclusive_price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    class Meta:
        model = RetailProductsVariations
        fields = "__all__"


    #TODO: validate this on the server
    @staticmethod
    def get_tax_percentage(instance):
        if instance.product.tax_rate != 0:
            tax_rate = instance.product.tax_rate
        elif instance.product.sub_category.tax_rate != 0:
            tax_rate = instance.product.sub_category.tax_rate
        elif instance.product.category.tax_rate != 0:
            tax_rate = instance.product.category.tax_rate
        else:
            tax_rate = 0
        return tax_rate
    
    def get_tax_amount(self, instance):
        tax_rate = self.get_tax_percentage(instance)
        tax_amount = 0
        if self.get_discount(instance=instance):
            discount_amount, discounted_amount = calculate_discount(self.get_discount(instance=instance), instance.price)
            actual_price = (float(discounted_amount) * 100)/(100+float(tax_rate))
            tax_amount = float(actual_price)*(float(tax_rate)/100)
        else:
            actual_price = (float(instance.price) * 100)/(100+float(tax_rate))
            tax_amount = float(actual_price)*float(tax_rate)/100
        return round(tax_amount, 2)

    def get_tax_exclusive_price(self, instance):
        tax_rate = self.get_tax_percentage(instance=instance)
        if self.get_discount(instance=instance):
            discount_amount, discounted_amount = calculate_discount(self.get_discount(instance=instance), instance.price)
            tax_exclusive_price = (int(discounted_amount) * 100)/(100+int(tax_rate))
        else:
            tax_exclusive_price = (int(instance.price) * 100)/(100+int(tax_rate))
        return round(tax_exclusive_price, 2)
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['variation'] = [{"id":each_product.id, "variation_type":each_product.variation_type.id, "variation_name":each_product.name,"variation_type_name":each_product.variation_type.name} 
                             for each_product in instance.variation.all()
                             ]
        data['variations_image'] = DetailProductsVariationsImageSerializer(
                instance.variations_image.all(),
                many=True,
                context=self.context
            ).data if instance.variations_image.all() else [DisplayRetailProductsImage(instance.product, many=False, context={"request":self.context.get('request')}).data]

        return data
    
    def get_customer_type(self, instance):
        request = self.context.get("request")
        #TODO: Decide how to decide between the types of Customers
        
        # if not request.user.orders:
        #     return "NEW CUSTOMER"
        # if request.user.orders:
        #     return "All Customer"
        # else:
        #     return "All Active Customer"

        return "All Customer"
    
    def get_discount(self, instance):
        # customer_type = self.get_customer_type
        current_time = timezone.now()
        product_discounts = VendorPlatformOffer.objects.filter(
            platform_offer__active = True,
            platform_offer__disabled = False,
            retail_product_variation = instance
        ).filter(
                Q(platform_offer__start_date__lte=current_time, platform_offer__end_date__gte=current_time)
            )
        if product_discounts:
            specific_discount = product_discounts.first()
            data = PlatformOfferForCartSerializer(specific_discount.platform_offer,
                                                   context = {"request":self.context.get("request"), "id":specific_discount.id},
                                                   many=False).data
            return data
        else:
            product_discounts = VendorPlatformOffer.objects.filter(
                platform_offer__active = True,
                platform_offer__disabled = False,
                retail_product = instance.product
            ).filter(
                    Q(platform_offer__start_date__lte=current_time, platform_offer__end_date__gte=current_time)
                )
            if product_discounts:
                specific_discount = product_discounts.first()
                data = PlatformOfferForCartSerializer(specific_discount.platform_offer,
                                                    context = {"request":self.context.get("request"), "id":specific_discount.id},
                                                    many=False).data
                return data
            else:
                product_discounts = RetailSaveOnItemsDiscountPercentage.objects.filter(
                        store_offer__disabled=False,
                        store_offer__active=True,
                        offer_category__in = instance.product.offer_categories.all()
                    ).filter(
                        Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                    )
                if product_discounts:
                    specific_discount = product_discounts.order_by('-discount_percentages').first()
                    data = RetailSaveOnItemsOfferForCartSerializer(specific_discount.store_offer, 
                                                        context = {"request":self.context.get("request"), "id":specific_discount.id} , 
                                                        many=False).data
                    return data
                else:
                    product_variation_discount = RetailSaveOnItemsDiscountPercentage.objects.filter(
                        store_offer__disabled=False,
                        store_offer__active=True,
                        retail_product_variation = instance
                    ).filter(
                        Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                    )

                    if product_variation_discount:
                        specific_discount = product_variation_discount.first()

                        data = RetailSaveOnItemsOfferForCartSerializer(specific_discount.store_offer, 
                                                            context = {"request":self.context.get("request"), "id":specific_discount.id} , 
                                                            many=False).data
                        return data
                    else:

                        product_discount = RetailSaveOnItemsDiscountPercentage.objects.filter(
                            store_offer__disabled=False,
                            store_offer__active=True,
                            retail_product = instance.product
                        ).filter(
                            Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                        )
                        if product_discount:
                            specific_discount = product_discount.first()

                            data = RetailSaveOnItemsOfferForCartSerializer(specific_discount.store_offer, 
                                                                context = {"request":self.context.get("request"), "id":specific_discount.id} , 
                                                                many=False).data
                            return data
                        else:
                            product_discount = RetailSaveOnItemsDiscountPercentage.objects.filter(store_offer__disabled=False, store_offer__active=True, sub_category = instance.product.sub_category, store_offer__vendor=instance.product.vendor).filter(
                                Q(store_offer__start_date__lte=current_time, store_offer__end_date__gte=current_time)
                                )
                            if product_discount:
                                specific_discount = product_discount.first()
                                return RetailSaveOnItemsOfferForCartSerializer(specific_discount.store_offer,
                                                            context = {"request":self.context.get("request"), "id":specific_discount.id} , 
                                                                many=False).data
                            else:
                                offer = RetailGetOneFreeOffer.objects.filter(disabled=False, active=True, retail_products = instance.product.id).filter(
                                    ( Q(start_date__lte=current_time, end_date__gte=current_time))
                                )
                                if offer:
                                    actual_discount =offer.first()
                                    
                                    return RetailGetOneFreeOfferForCartSerializer(actual_discount, many=False).data
                                else:
                                    store_offer = RetailStoreOffer.objects.filter(disabled=False, active=True, vendor = instance.product.vendor).filter(
                                        Q(start_date__lte=current_time, end_date__gte=current_time)
                                        )
                                    if store_offer:
                                        actual_offer = store_offer.first()
                                        return RetailStoreOfferForCartSerializer(actual_offer, many=False).data

class UserRetailCartSerializer(serializers.ModelSerializer):
    retail_product_variation = serializers.SerializerMethodField()
    product_disabled = serializers.SerializerMethodField()

    class Meta:
        model = RetailCart
        fields = "__all__"
    
    def get_product_disabled(self, obj):
        if obj.retail_product_variation.disabled == True or obj.retail_product_variation.product.disabled == True:
            return True
        return False
    
    def get_retail_product_variation(self, obj):
        serializer = RetailProductsVariationsDetailSerializer( obj.retail_product_variation, context={"request": self.context.get("request")})
        return serializer.data
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if data["retail_product_variation"]["discount"]:
            actual_price = data["retail_product_variation"]["price"]
            discount_amount, discounted_amount = calculate_discount(data["retail_product_variation"]["discount"], actual_price)

            data["retail_product_variation"]["discount_amount"] = round(discount_amount, 2)
            data["retail_product_variation"]["discounted_amount"] = round(discounted_amount, 2)

        return data

class RetailCartCalculationSerializer(serializers.Serializer):
    # retail_cart = UserRetailCartSerializer(many=True)
    
    def to_representation(self, instance):
        data = UserRetailCartSerializer(instance,  context={"request": self.context.get("request")}).data
        data["retail_product_variation"]["product"] = [{"id": instance.retail_product_variation.product.id, "product_name":instance.retail_product_variation.product.name, "vendor_id":instance.retail_product_variation.product.vendor.id, "vendor_name":instance.retail_product_variation.product.vendor.vendor_name, "disabled":instance.retail_product_variation.product.disabled}]
        return data


class RetailDeliveryChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailDeliveryCharge
        fields = "__all__"



        



        