from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from retail.models import RetailProducts, RetailProductsVariations
from retail.serializers import ProductsVariationsImageSerializer, RetailProductsImage
from retail_logistics.models import DeliveryDriver
from retail_marketplace.models import RetailCart
from retail_offers.models import RetailLoyaltyPrograms
from retail_review.models import Review
from user.models import User
from vendor.models import Vendor

from .models import OrderStatus, OrderedProduct, OrderedProductStatus, RetailOrder, RetailPayment, RetailPaymentInfo, RetailVendorOrder


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = "__all__"


class RetailPaymentsSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = RetailPayment

class RetailPaymentInfoSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = RetailPaymentInfo

class DetailRetailProductsSerializer(ModelSerializer):
    class Meta:
        fields = ['name']
        model = RetailProducts

class DetailRetailProductsVariationsSerializer(ModelSerializer):
    product = DetailRetailProductsSerializer()
    class Meta:
        fields = "__all__"
        model = RetailProductsVariations
        read_only_fields = ['created_date','updated_date', 'tax_exclusive_price', 'tax_amount']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['variation'] = [{"id":each_product.id, "variation_type":each_product.variation_type.id, "variation_name":each_product.name,"variation_type_name":each_product.variation_type.name} 
                             for each_product in instance.variation.all()
                             ]
        data['variations_image'] = ProductsVariationsImageSerializer(
                instance.variations_image.all(),
                many=True,
                context=self.context
            ).data if instance.variations_image.exists() else [RetailProductsImage(instance.product, many=False, context={"request":self.context.get('request')}).data]
        return data

class DeliveryDriverDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryDriver
        fields = ["id", "name", "primary_phone_number", "secondary_phone_number", "vehicle_model", "vehicle_number", "license_number"]

class DetailOrderedProductStatusSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer()
    delivery_driver = DeliveryDriverDetailSerializer()

    class Meta:
        model = OrderedProductStatus
        fields = "__all__"

class DetailRetailLoyaltyProgramsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailLoyaltyPrograms
        fields = "__all__"

class DetailUserReviewSerializer(ModelSerializer):
    class Meta:
        fields="__all__"
        model=Review

class RetailOrderedProductSerializer(ModelSerializer):
    product_variation = serializers.PrimaryKeyRelatedField( queryset = RetailProductsVariations.objects.all(), write_only=True)
    retail_product_variation_details = serializers.SerializerMethodField() 
    status = DetailOrderedProductStatusSerializer(read_only=True, many=True)
    loyalty_discount = serializers.SerializerMethodField()
    coupon_discount = serializers.SerializerMethodField()
    total_discounted_amount = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()
    special_request = serializers.SerializerMethodField()

    class Meta:
        fields="__all__"
        model=OrderedProduct
    
    def get_review(self, obj):
        review = Review.objects.filter(ordered_product=obj.id).first()
        if review:
            review_serializer = DetailUserReviewSerializer(review, context={"request":self.context.get("request")})
            return review_serializer.data
        return None

    def get_retail_product_variation_details(self, obj):
        retail_product_variation_details = DetailRetailProductsVariationsSerializer(obj.product_variation,  context={"request":self.context.get("request")})
        return retail_product_variation_details.data
    
    def get_loyalty_discount(self, obj):
        loyalty_program = obj.order.loyalty_program
        serializer = DetailRetailLoyaltyProgramsSerializer(loyalty_program)
        return serializer.data
    
    def get_coupon_discount(self, obj):
        return obj.vendor_order.vendor_coupon_discount + obj.vendor_order.admin_coupon_discount
    
    def get_total_discounted_amount(self, obj):
        price = obj.price
        if obj.discounted_amount != 0:
            price = obj.discounted_amount
        
        total_discounted_amount = price - self.get_coupon_discount(obj)
        return total_discounted_amount
    
    def get_tax_amount(self, obj):
        price = obj.price
        if obj.discounted_amount:
            price = obj.discounted_amount
        tax_exclusive_amount = obj.tax_exclusive_amount
        tax_amount = price - tax_exclusive_amount
        return round(tax_amount,2)
    
    def get_special_request(self, obj):
        product_variation_id= obj.product_variation.id
        carts = obj.order.carts.all()
        for cart in carts:
            if product_variation_id == cart.retail_product_variation.id:
                return cart.special_request
        return None

class RetailVendorOrdersSerializer(ModelSerializer):
    ordered_product = serializers.PrimaryKeyRelatedField( queryset=OrderedProduct.objects.all(), write_only=True)
    ordered_product_details = serializers.SerializerMethodField()

    tax_exclusive_amount = serializers.SerializerMethodField()
    
    class Meta:
        fields ="__all__"
        model = RetailVendorOrder
    
    def get_ordered_product_details(self,obj):
        ordered_product_details = RetailOrderedProductSerializer(obj.ordered_product, many=True,  context={"request":self.context.get("request")})
        return ordered_product_details.data
    
    def get_tax_exclusive_amount(self, obj):
        ordered_product_details = RetailOrderedProductSerializer(obj.ordered_product, many=True,  context={"request":self.context.get("request")}).data
        tax_exclusive_amount=0
        for product in ordered_product_details:
            tax_exclusive_amount += product['tax_exclusive_amount']
        return tax_exclusive_amount

class RetailOrdersSerializer(ModelSerializer):
    retail_order_vendor = RetailVendorOrdersSerializer(many=True, required=False)
    class Meta:
        fields = "__all__"
        model = RetailOrder

class DetailVendorOrderSerializer(ModelSerializer):
    retail_order_vendor = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = RetailOrder
    
    def get_retail_order_vendor(self, obj):
        request = self.context.get('request')
        vendor_order = RetailVendorOrder.objects.filter(order=obj, vendor=request.user.user)
        serializer = RetailVendorOrdersSerializer(vendor_order, many=True, required=False,context={"request":self.context.get("request")} )
        return serializer.data


class DetailRetailOrderedProductSerializer(serializers.ModelSerializer):
    product_variation = serializers.PrimaryKeyRelatedField( queryset = RetailProductsVariations.objects.all(), write_only=True)
    retail_product_variation_details = serializers.SerializerMethodField() 
    coupon_discount = serializers.SerializerMethodField()
    total_discounted_amount = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    vendor_detail = serializers.SerializerMethodField()
    special_request = serializers.SerializerMethodField()

    class Meta:
        fields="__all__"
        model=OrderedProduct
    
    def get_vendor_detail(self, obj):
        vendor = Vendor.objects.get(id=obj.vendor_order.vendor.id)
        return {
            "vendor_id": vendor.id,
            "name": vendor.vendor_name,
            "address": vendor.vendor_location,
            "phone": vendor.user_profile.phone_number
        }

    def get_retail_product_variation_details(self, obj):
        retail_product_variation_details = DetailRetailProductsVariationsSerializer(obj.product_variation,  context={"request":self.context.get("request")})
        return retail_product_variation_details.data
    
    def get_coupon_discount(self, obj):
        return obj.vendor_order.vendor_coupon_discount + obj.vendor_order.admin_coupon_discount
    
    def get_total_discounted_amount(self, obj):
        price = obj.price
        if obj.discounted_amount != 0:
            price = obj.discounted_amount
        
        total_discounted_amount = price - self.get_coupon_discount(obj)
        return total_discounted_amount
    
    def get_tax_amount(self, obj):
        price = obj.price
        if obj.discounted_amount:
            price = obj.discounted_amount
        tax_exclusive_amount = obj.tax_exclusive_amount
        tax_amount = price - tax_exclusive_amount
        return round(tax_amount,2)
    
    def get_special_request(self, obj):
        product_variation_id= obj.product_variation.id
        carts = obj.order.carts.all()
        for cart in carts:
            if product_variation_id == cart.retail_product_variation.id:
                return cart.special_request
        return None

class DetailOrderStatusUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email"]

class OrderedProductStatusSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField( queryset=OrderStatus.objects.all(),  write_only=True)
    status_detail = OrderStatusSerializer(source='status', read_only=True)

    ordered_product = serializers.PrimaryKeyRelatedField(queryset=OrderedProduct.objects.all(), write_only=True)
    ordered_product_detail = DetailRetailOrderedProductSerializer(source='ordered_product', read_only=True)

    delivery_driver = serializers.PrimaryKeyRelatedField(queryset=DeliveryDriver.objects.all(), write_only=True)
    delivery_driver_detail = DeliveryDriverDetailSerializer(source='delivery_driver', read_only=True)

    created_by = DetailOrderStatusUserSerializer(read_only=True)

    class Meta:
        model = OrderedProductStatus
        fields = "__all__"
        read_only_fields = ['created_by']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    

#ADMIN serializer

class AdminOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = '__all__'

class AdminOrderedProductStatusSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField( queryset=OrderStatus.objects.all(),  write_only=True)
    status_detail = AdminOrderStatusSerializer(source='status', read_only=True)

    ordered_product = serializers.PrimaryKeyRelatedField(queryset=OrderedProduct.objects.all(), write_only=True)
    ordered_product_detail = serializers.SerializerMethodField()

    delivery_driver = serializers.PrimaryKeyRelatedField(queryset=DeliveryDriver.objects.all(), write_only=True)
    delivery_driver_detail = DeliveryDriverDetailSerializer(source='delivery_driver', read_only=True)

    created_by = DetailOrderStatusUserSerializer(read_only=True)
    
    delivery_details = serializers.SerializerMethodField()

    def get_ordered_product_detail(self, obj):
        return DetailRetailOrderedProductSerializer(obj.ordered_product, context={"request": self.context.get('request')}).data

    class Meta:
        model = OrderedProductStatus
        fields = "__all__"
        read_only_fields = ['created_by']
    
    def get_delivery_details(self, obj):
        order = obj.ordered_product.order
        details = {
            "first_name" : order.first_name,
            "last_name" : order.last_name,
            "phone" : order.phone,
            "email" : order.email,
            "address" : order.address,
            "country" : order.country,
            "state" : order.state,
            "city" : order.city,
            "pin_code" : order.pin_code
        }
        return details

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        response = super().create(validated_data)

        order = RetailOrder.objects.get(id=response.ordered_product.order.id)
        ordered_product = OrderedProduct.objects.get(id=response.ordered_product.id)
        

        if response.status.status_code == "002":
            ordered_product.ordered_product_status = "Accepted"
            ordered_product.save()
        
        if response.status.status_code == "011":
            ordered_product.ordered_product_status = "Completed"
            ordered_product.save()

            if order.payment_method == "Cash On Delivery":
                payment = RetailPayment.objects.get(id=order.payment.id)
                payment.status = "COMPLETE"
                payment.save()

        if response.status.status_code == "009":
            ordered_product.ordered_product_status = "Cancelled"
            ordered_product.save()

        return response

class AdminOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailOrder
        fields = ['id', 'order_number', 'first_name', 'last_name', 'phone']

class AdminRetailOrderedProductSerializer(serializers.ModelSerializer):
    product_variation = serializers.PrimaryKeyRelatedField( queryset = RetailProductsVariations.objects.all(), write_only=True)
    retail_product_variation_details = serializers.SerializerMethodField() 
    status = DetailOrderedProductStatusSerializer(read_only=True, many=True)
    loyalty_discount = serializers.SerializerMethodField()
    coupon_discount = serializers.SerializerMethodField()
    total_discounted_amount = serializers.SerializerMethodField()
    special_request = serializers.SerializerMethodField()
    delivery_charge = serializers.SerializerMethodField()
    delivery_detail = serializers.SerializerMethodField()

    class Meta:
        fields="__all__"
        model=OrderedProduct

    def get_retail_product_variation_details(self, obj):
        retail_product_variation_details = DetailRetailProductsVariationsSerializer(obj.product_variation,  context={"request":self.context.get("request")})
        return retail_product_variation_details.data
    
    def get_loyalty_discount(self, obj):
        loyalty_program = obj.order.loyalty_program
        serializer = DetailRetailLoyaltyProgramsSerializer(loyalty_program)
        return serializer.data
    
    def get_coupon_discount(self, obj):
        return obj.vendor_order.vendor_coupon_discount + obj.vendor_order.admin_coupon_discount
    
    def get_total_discounted_amount(self, obj):
        price = obj.price
        if obj.discounted_amount != 0:
            price = obj.discounted_amount
        
        total_discounted_amount = price - self.get_coupon_discount(obj)
        return total_discounted_amount
    
    def get_special_request(self, obj):
        product_variation_id= obj.product_variation.id
        carts = obj.order.carts.all()
        for cart in carts:
            if product_variation_id == cart.retail_product_variation.id:
                return cart.special_request
        return None
    
    def get_delivery_charge(self, obj):
        return obj.vendor_order.delivery_charge if obj.vendor_order.delivery_charge else None
    
    def get_delivery_detail(self, obj):
        return {
            "first_name": obj.order.first_name,
            "last_name": obj.order.last_name,
            "phone": obj.order.phone,
            "email": obj.order.email,
            "address": obj.order.address,
            "country": obj.order.country,
            "state": obj.order.state,
            "city": obj.order.city,
            "pin_code": obj.order.pin_code
        }
    