from rest_framework import serializers

from retail.models import RefundPolicy, RetailProducts, RetailProductsVariations
from retail.serializers import RefundPolicySerializer
from retail_logistics.models import DeliveryDriver
from retail_orders.models import OrderedProduct, RetailOrder
from retail_refund.models import RefundProductStatus, RefundStatus, RetailRefund, RetailRefundItem
from user.models import User

class RefundStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundStatus
        fields = "__all__"

class RefundDeliveryDriverDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryDriver
        fields = ["id", "name", "primary_phone_number", "secondary_phone_number", "vehicle_model", "vehicle_number", "license_number"]

class DetailRefundProductStatusSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField( queryset=RefundStatus.objects.all(),  write_only=True)
    status_detail = RefundStatusSerializer(source='status', read_only=True)
    delivery_driver = RefundDeliveryDriverDetailSerializer(read_only=True)

    class Meta:
        model = RefundProductStatus
        fields = "__all__"

class RetailRefundItemSerializer(serializers.ModelSerializer):
    refund_status = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = RetailRefundItem
    
    def get_refund_status(self, obj):
        status = obj.refund_status.order_by('created_at')
        return DetailRefundProductStatusSerializer(status, many=True).data

class RetailProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailProducts
        fields = ['default_image','image_1','image_2','image_3']

class DetailRetailRefundItemSerializer(serializers.ModelSerializer):
    product_variation = serializers.PrimaryKeyRelatedField( queryset=RetailProductsVariations.objects.all(), write_only=True)
    product_variation_detail = serializers.SerializerMethodField()

    refund_status = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = RetailRefundItem
    
    def get_refund_status(self, obj):
        status = obj.refund_status.order_by('created_at')
        return DetailRefundProductStatusSerializer(status, many=True).data
    
    def get_product_variation_detail(self, obj):
        order = self.context.get('order')
        ordered_product = OrderedProduct.objects.filter(order=order).filter(product_variation=obj.product_variation).first()
        if ordered_product:
            image_1 = None
            image_2 = None
            image_3 = None
            default_image = None
            if ordered_product.product_variation.product.default_image:
                default_image = RetailProductImageSerializer(ordered_product.product_variation.product, context={'request':self.context.get('request')}).data['default_image']
            if ordered_product.product_variation.product.image_1:
                image_1 = RetailProductImageSerializer(ordered_product.product_variation.product, context={'request':self.context.get('request')}).data['image_1']
            if ordered_product.product_variation.product.image_2:
                image_2 = RetailProductImageSerializer(ordered_product.product_variation.product, context={'request':self.context.get('request')}).data['image_2']
            if ordered_product.product_variation.product.image_3:
                image_3 = RetailProductImageSerializer(ordered_product.product_variation.product, context={'request':self.context.get('request')}).data['image_3']

            refund_policies = ordered_product.product_variation.product.refund_policies.all()
            if refund_policies:
                refund_policies = RefundPolicySerializer(refund_policies, many=True).data

            return {
                "product_name": ordered_product.product_variation.product.name,
                "price": ordered_product.price,
                "discounted_amount":ordered_product.discounted_amount,
                "default_image" : default_image,
                "image_1" : image_1,
                "image_2" : image_2,
                "image_3" : image_3,
                "refund_policies" : refund_policies
            }
        return {
                "product_name": None,
                "price": None,
                "discounted_amount": None
            }

class RetailRefundSerializer(serializers.ModelSerializer):
    refund_products = RetailRefundItemSerializer(many=True, write_only=True)
    refund_products_detail = serializers.SerializerMethodField()

    ordered_products = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = RetailRefund
        read_only_fields = ['user']
    
    def get_refund_products_detail(self, obj):
        refund_products = obj.refund_products.all()
        data = []
        for refund_product in refund_products:
            serializer = DetailRetailRefundItemSerializer(refund_product, context={'order':obj.order, 'request':self.context.get('request')}).data
            data.append(serializer)
        return data
    
    def get_ordered_products(self, obj):
        ids = []
        ordered_products = obj.order.order_products.all()
        for product in ordered_products:
            ids.append(product.id)
        return ids
        

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user

        order = attrs.get('order')
        if order:
            try:
                order = RetailOrder.objects.get(id=order.id)
            except RetailOrder.DoesNotExist:
                raise serializers.ValidationError({"message": "Order does not exist"})
            
            if order.user != user:
                raise serializers.ValidationError({"message": "Invalid Order"})
        
        product = attrs.get("refund_products")
        for item in product:
            refund = RetailRefund.objects.filter(order=order, refund_products__product_variation = item['product_variation']).exists()
            if refund:
                raise serializers.ValidationError({"message": f"Product {item['product_variation']} has already been refunded for this order."})
            
        return super().validate(attrs)
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user

        refund_products_data = validated_data.pop('refund_products', "")

        retail_refund = RetailRefund.objects.create(**validated_data)

        for refund_product_data in refund_products_data:
            refund_item = RetailRefundItem.objects.create(**refund_product_data)
            retail_refund.refund_products.add(refund_item)
            
            try:
                refund_status = RefundStatus.objects.get(status_code='001')
            except RefundStatus.DoesNotExist:
                refund_status = RefundStatus.objects.create(
                    status = "initial status",
                    status_code = "001"
                )

            refund_product_status = RefundProductStatus.objects.create(
                refund_product = refund_item,
                status = refund_status,
                created_by = request.user
            )

        return retail_refund

class RefundPolicyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundPolicy
        fields = ['id','policy', 'description']

class RetailProductDetailSerializer(serializers.ModelSerializer):
    refund_policies = RefundPolicyDetailSerializer(many=True)
    class Meta:
        model =RetailProducts
        fields = ['id', 'name', 'refund_policies']
        
class ProductVariationDetailSerializer(serializers.ModelSerializer):
    product = RetailProductDetailSerializer()
    class Meta:
        model = RetailProductsVariations
        fields = ['id', 'product']

class DetailRetailRefundItemsSerializer(serializers.ModelSerializer):
    product_variation = ProductVariationDetailSerializer()
    class Meta:
        fields = "__all__"
        model = RetailRefundItem

class DetailRefundStatusUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email"]
    
class RefundProductStatusSerializer(serializers.ModelSerializer):
    refund_product = serializers.PrimaryKeyRelatedField(queryset=RetailRefundItem.objects.all(), write_only=True)
    refund_product_detail = DetailRetailRefundItemsSerializer(source='refund_product', read_only=True)

    status = serializers.PrimaryKeyRelatedField( queryset=RefundStatus.objects.all(),  write_only=True)
    status_detail = RefundStatusSerializer(source='status', read_only=True)

    delivery_driver = serializers.PrimaryKeyRelatedField(queryset=DeliveryDriver.objects.all(), write_only=True)
    delivery_driver_detail = RefundDeliveryDriverDetailSerializer(source='delivery_driver', read_only=True)

    created_by = DetailRefundStatusUserSerializer(read_only=True)

    class Meta:
        model = RefundProductStatus
        fields = "__all__"
        read_only_fields = ['created_by' ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)