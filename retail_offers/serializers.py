from rest_framework import serializers
from django.db.models import Q

from retail.models import ProductsVariationsImage, RetailProducts
from user.models import UserProfile

from .models import OfferCategory, PlatformOffer, RetailCoupon, RetailLoyaltyPrograms, RetailStoreOffer, RetailGetOneFreeOffer, RetailSaveOnItemsOffer, RetailSaveOnItemsDiscountPercentage, VendorPlatformOffer

class ReatilStoreOfferSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RetailStoreOffer
        fields = "__all__"
        read_only_fields = ['created_date','active']
    
    def validate(self, attrs):
        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")
        if not discount_start_date and discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})
        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"The discount start date is smaller than discount start date"})
        
        discounts = RetailStoreOffer.objects.filter( disabled=False, active=True).filter(vendor=attrs.get('vendor')).filter(
            Q(start_date__range=(discount_start_date, discount_end_date)) | 
            Q(end_date__range=(discount_start_date, discount_end_date)) |
            Q(start_date__lte=discount_start_date, end_date__gte=discount_end_date)
            )
        if discounts.exists():
            raise serializers.ValidationError({"message":f"Store offer already exists for the selected date"})
        
        return super().validate(attrs)
    

class RetailGetOneFreeOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailGetOneFreeOffer
        fields = "__all__"
        read_only_fields = ['created_date','active']
    
    def validate(self, attrs):
        request = self.context.get('request')
        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")
        vendor = request.user.user

        if not discount_start_date and discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})
        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"The discount start date is smaller than discount start date"})
        
        offer_products = attrs.get("retail_products","")
        for each_product in offer_products:
            if each_product.vendor != vendor:
                raise serializers.ValidationError({"msg":"product item does not belong to the vendor"})
            
            retail_product = RetailGetOneFreeOffer.objects.filter(retail_products = each_product, disabled=False, active=True).filter(
                Q(start_date__range=(discount_start_date, discount_end_date)) | 
                Q(end_date__range=(discount_start_date, discount_end_date)) |
                Q(start_date__lte=discount_start_date, end_date__gte=discount_end_date)
                )
            
            if self.instance:
                retail_product = retail_product.exclude(id=self.instance.id)

            if retail_product.exists():
                raise serializers.ValidationError({"message":f"Product {each_product} already has a offer existing"})
                
        return super().validate(attrs)
    
    def to_representation(self, instance):
        data =  super().to_representation(instance)
        data['retail_products'] = [{"product_name":RetailProducts.objects.get(id=item).name, "product_id":RetailProducts.objects.get(id=item).id} for item in data['retail_products']]
        return data
    
class RetailSaveOnItemsDiscountPercentageSerializer(serializers.ModelSerializer):
    discount_on =  serializers.SerializerMethodField(read_only = True)
        
    def get_discount_on(self, instance):
        if instance.retail_product:
            return "retail_product"
        elif instance.sub_category:
            return "sub_category"
        else:
            return "retail_product_variation"

    class Meta:
        model = RetailSaveOnItemsDiscountPercentage
        fields = ['id', 'store_offer', 'discount_percentages', 'retail_product', 'sub_category', 'retail_product_variation','offer_category', 'discount_on']
        read_only_fields = ['store_offer']

class RetailSaveOnItemsOfferSerializer(serializers.ModelSerializer):
    offer_items = RetailSaveOnItemsDiscountPercentageSerializer(many=True, allow_null=True, required=False)

    class Meta:
        model = RetailSaveOnItemsOffer
        fields = "__all__"
        read_only_fields = ['created_date','active']
    
    def validate(self, attrs):
        request = self.context.get("request")

        offer_items = attrs.get('offer_items',[])
        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")

        if not discount_start_date or not discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})

        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"The discount start date is smaller than discount start date"})
        
        for each_item in offer_items:
            retail_product_variation = each_item.get("retail_product_variation",None)
            retail_product = each_item.get('retail_product',None)
            sub_category = each_item.get('sub_category',None)
            offer_category = each_item.get('offer_category', None)
            old_id = each_item.get('old_id',None)

            if sum([retail_product_variation is not None, retail_product is not None, sub_category is not None]) > 1:
                raise serializers.ValidationError({"msg":"Only one of product variation, retail product, or category can have a value."})
            
            if offer_category:
                if offer_category.vendor != attrs.get('vendor'):
                    raise serializers.ValidationError({"msg":"product does not belong to the vendor"})
                product_item = RetailSaveOnItemsDiscountPercentage.objects.filter(offer_category=offer_category, store_offer__disabled=False, store_offer__active=True).filter(
                    Q(store_offer__start_date__range=(discount_start_date, discount_end_date)) | 
                    Q(store_offer__end_date__range=(discount_start_date, discount_end_date)) |
                    Q(store_offer__start_date__lte=discount_start_date, store_offer__end_date__gte=discount_end_date)
                    ).exclude(id=old_id)
                
                if product_item.exists():
                    raise serializers.ValidationError({"message":f" {offer_category} already has a offer existing"})

            
            if retail_product:
                if retail_product.vendor != attrs.get('vendor'):
                    raise serializers.ValidationError({"msg":"product does not belong to the vendor"})
                product_item = RetailSaveOnItemsDiscountPercentage.objects.filter(retail_product=retail_product, store_offer__disabled=False, store_offer__active=True).filter(
                    Q(store_offer__start_date__range=(discount_start_date, discount_end_date)) | 
                    Q(store_offer__end_date__range=(discount_start_date, discount_end_date)) |
                    Q(store_offer__start_date__lte=discount_start_date, store_offer__end_date__gte=discount_end_date)
                    ).exclude(id=old_id)
                
                if product_item.exists():
                    raise serializers.ValidationError({"message":f"Product {retail_product} already has a offer existing"})
            
            if sub_category:
                if sub_category.vendor!= attrs.get('vendor'):
                    raise serializers.ValidationError({"msg":"category deos not belong to the vendor"})
                sub_category_item = RetailSaveOnItemsDiscountPercentage.objects.filter(sub_category=sub_category, store_offer__disabled=False, store_offer__active=True).filter(
                    Q(store_offer__start_date__range=(discount_start_date, discount_end_date)) | 
                    Q(store_offer__end_date__range=(discount_start_date, discount_end_date)) |
                    Q(store_offer__start_date__lte=discount_start_date, store_offer__end_date__gte=discount_end_date)
                    ).exclude(id=old_id)
                
                if sub_category_item.exists():
                    raise serializers.ValidationError({"message":f"Category {sub_category} already has a offer existing"})
            
            if retail_product_variation:
                if retail_product_variation.product.vendor!= attrs.get('vendor'):
                    raise serializers.ValidationError({"msg":"product variation deos not belong to the vendor"})
                retail_product_variation_item = RetailSaveOnItemsDiscountPercentage.objects.filter(retail_product_variation=retail_product_variation, store_offer__disabled=False, store_offer__active=True).filter(
                    Q(store_offer__start_date__range=(discount_start_date, discount_end_date)) | 
                    Q(store_offer__end_date__range=(discount_start_date, discount_end_date)) |
                    Q(store_offer__start_date__lte=discount_start_date, store_offer__end_date__gte=discount_end_date)
                    ).exclude(id=old_id)
        
                if retail_product_variation_item.exists():
                    raise serializers.ValidationError({"message":f"Product variation {retail_product_variation} already has a offer existing"})
            
        return super().validate(attrs)
    
    def create(self, validated_data):
        offer_items = validated_data.pop('offer_items',[])
        
        instance =  RetailSaveOnItemsOffer.objects.create(**validated_data)
        for each_items in offer_items:
            RetailSaveOnItemsDiscountPercentage.objects.create(**each_items, store_offer = instance)
        return instance
    
    def update(self, instance, validated_data):
        offer_items = validated_data.pop('offer_items',"")
        for each_item in offer_items:
            if each_item.get("old_id",None):
                offer_item = RetailSaveOnItemsDiscountPercentage.objects.filter(store_offer__disabled=False, store_offer__active=True).get(id=each_item.pop('old_id'))
               

                test = RetailSaveOnItemsDiscountPercentageSerializer(offer_item, each_item, partial=True)
                
                if test.is_valid(raise_exception=True):
                    test.save()
            else:
                RetailSaveOnItemsDiscountPercentage.objects.create(**each_item, store_offer = instance)

        return super().update(instance, validated_data)
    
    
class DisableRetailStoreOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["disabled"]
        model = RetailStoreOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.disabled = True
        instance.save()
        return instance

class DisableRetailGetOneFreeOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["disabled"]
        model = RetailGetOneFreeOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.disabled = True
        instance.save()
        return instance

class DisableRetailSaveOnItemsOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["disabled"]
        model = RetailSaveOnItemsOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.disabled = True
        instance.save()
        return instance

class RetailCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailCoupon
        fields = "__all__"
        read_only_fields = ['chowchow_coupon']
    
    def create(self, validated_data):
        request = self.context.get('request', '')
        instance = super().create(validated_data)

        if request.user.is_superuser:
            instance.chowchow_coupon = True
            instance.save()
        
        return instance


class RetailLoyaltyProgramsSerializer(serializers.ModelSerializer):
    valid = serializers.SerializerMethodField()
    class Meta:
        model = RetailLoyaltyPrograms
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
        
class OfferCategorySerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        queryset=RetailProducts.objects.all(),
        many=True
    )
    class Meta:
        model = OfferCategory
        fields = '__all__'
        read_only_fields = ['category_slug', 'vendor']

    def validate(self, attrs):
        user = self.context.get('request').user
        vendor = user.user
        products = attrs.get('products', '')
        if products:
            for product in products:
                if product.vendor != vendor:
                    raise serializers.ValidationError({"msg": f"Product '{product.name}' donot belong to this vendor" }) 
        return super().validate(attrs)
    
    def create(self, validated_data):
        request = self.context.get('request')
        product_data = validated_data.pop('products', [])
        validated_data['vendor'] = request.user.user

        data = OfferCategory.objects.create(**validated_data)

        if product_data:
            data.products.set(product_data)
        return data
    
    def update(self, instance, validated_data):
        products = validated_data.pop('products', '')
        if products:
            instance.products.clear()
            instance.products.set(products)
        return super().update(instance, validated_data)

class PlatformOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformOffer
        fields = '__all__'
        read_only_fields = ['created_by']
    
    def validate(self, attrs):
        request = self.context.get("request")

        discount_start_date = attrs.get('start_date',"")
        discount_end_date = attrs.get('end_date',"")

        if not discount_start_date and discount_end_date:
            raise serializers.ValidationError({"message":"Discount start and end date both should be provided"})

        if (discount_end_date < discount_start_date) :
            raise serializers.ValidationError({"message":"The discount start date is smaller than discount start date"})
        
        return super().validate(attrs)
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)

class VendorPlatformOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPlatformOffer
        fields = '__all__'
        read_only_fields = ['vendor']

class CreateMultipleVendorPlatformOfferSerializer(serializers.Serializer):
    offers = VendorPlatformOfferSerializer(many=True)

    def to_representation(self, instance):
        return instance
    
    def validate(self, attrs):
        request = self.context.get('request')
        offers = attrs.get('offers')
        vendor = request.user.user

        for offer in offers:
            retail_product = offer.get('retail_product')
            retail_product_variation = offer.get('retail_product_variation')
            platform_offer = offer.get('platform_offer')

            start_date = platform_offer.start_date
            end_date = platform_offer.end_date

            if retail_product and retail_product_variation:
                raise serializers.ValidationError({'message': 'Only one of retail product or retail product variation can have value'})

            if retail_product:
                if VendorPlatformOffer.objects.filter(platform_offer__active=True, platform_offer__disabled=False,  vendor=vendor, retail_product_variation__in = retail_product.products_variations.all()).exclude(
                    platform_offer__end_date__lt=start_date
                    ).exclude(
                        platform_offer__start_date__gt=end_date
                    ).exists():
                    raise serializers.ValidationError({'message': f'Product variation associated with {retail_product.name} product already listed in platform offers.'})


                if VendorPlatformOffer.objects.filter(platform_offer__active=True, platform_offer__disabled=False,  vendor=vendor, retail_product=retail_product).exclude(
                    platform_offer__end_date__lt=start_date
                    ).exclude(
                        platform_offer__start_date__gt=end_date
                    ).exists():
                    raise serializers.ValidationError({'message': f'This product {retail_product.name} is already associated with the platform offer for this vendor.'})

            if retail_product_variation:
                if VendorPlatformOffer.objects.filter(platform_offer__active=True, platform_offer__disabled=False, vendor=vendor, retail_product__products_variations__in = [retail_product_variation]).exclude(
                    platform_offer__end_date__lt=start_date
                ).exclude(
                    platform_offer__start_date__gt=end_date
                ).exists():
                    raise serializers.ValidationError({'message': f'Product for {retail_product_variation.sku} variation already exists in platform offer'})
                    
                if VendorPlatformOffer.objects.filter(platform_offer__active=True, platform_offer__disabled=False,  vendor=vendor, retail_product_variation=retail_product_variation).exclude(
                    platform_offer__end_date__lt=start_date
                ).exclude(
                    platform_offer__start_date__gt=end_date
                ).exists():
                    raise serializers.ValidationError({'message': f'This product variation {retail_product_variation.sku} is already associated with the platform offer for this vendor.'})
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        offers = validated_data.get('offers')
        returned_items = []
        for offer in offers:
            offer['vendor'] = request.user.user
            data = VendorPlatformOffer.objects.create(**offer)

            returned_items.append(VendorPlatformOfferSerializer(data, many=False, context={"request":self.context.get("request")}).data)
        return {
            "offers": returned_items
        }   

class OfferProductsVariationsImageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ProductsVariationsImage
        read_only_fields = ['variations','created_date']

class OfferRetailProductsImage(serializers.ModelSerializer):
    class Meta:
        fields = ["default_image"]
        model = RetailProducts

class DetailVendorPlatformOfferSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = VendorPlatformOffer
        fields = ['id', 'product', 'discount_percentages', 'platform_offer', 'vendor']
    
    def get_product(self, instance):
        if instance.retail_product:
            product = {
                "id" : instance.retail_product.id,
                "name": instance.retail_product.name,
                "sub_category": instance.retail_product.sub_category.id,
                "products_variations": [
                    {
                        "id" : variation.id,
                        "sku": variation.sku,
                        "price": variation.price,
                        "discount_percentage": instance.discount_percentages,
                        "discounted_amount": float(instance.discount_percentages / 100) * float(variation.price),
                        "variations_image" : OfferProductsVariationsImageSerializer(
                                variation.variations_image.all(),
                                many=True,
                                context=self.context
                            ).data if variation.variations_image.exists() else [OfferRetailProductsImage(variation.product, many=False, context={"request":self.context.get('request')}).data]
                    }
                    for variation in instance.retail_product.products_variations.all()
                ]
            }
        if instance.retail_product_variation:
            product = {
                "id" : instance.retail_product_variation.product.id,
                    "name": instance.retail_product_variation.product.name,
                    "sub_category" : instance.retail_product_variation.product.sub_category.id,
                    "products_variations" : [{
                        "id" : instance.retail_product_variation.id,
                        "sku" : instance.retail_product_variation.sku,
                        "price" : instance.retail_product_variation.price,
                        "discount_percentage" : instance.discount_percentages,
                        "discounted_amount" : float(instance.discount_percentages/100) * float(instance.retail_product_variation.price),
                        "variations_image" : OfferProductsVariationsImageSerializer(
                                instance.retail_product_variation.variations_image.all(),
                                many=True,
                                context=self.context
                            ).data if instance.retail_product_variation.variations_image.exists() else [OfferRetailProductsImage(instance.retail_product_variation.product, many=False, context={"request":self.context.get('request')}).data]
                    }]
            }
        return  product
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['platform_offer'] = {
            "id" : instance.platform_offer.id,
            "name" : instance.platform_offer.offer_name
        }
        return data


class PlatformOfferProductSerializer(serializers.ModelSerializer):
    vendor_platform_offer = serializers.SerializerMethodField()

    class Meta:
        model = PlatformOffer
        fields = '__all__'
    
    def get_vendor_platform_offer(self, obj):
        request = self.context.get('request')
        return DetailVendorPlatformOfferSerializer(obj.vendor_platform_offer.all() , context={'request':request}, many=True).data

class DisableRetailCouponSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["disabled"]
        model = RetailCoupon
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.disabled = True
        instance.save()
        return instance

class DisableRetailLoyaltyProgramsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["disabled"]
        model = RetailLoyaltyPrograms
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.disabled = True
        instance.save()
        return instance

class DisablePlatformOfferSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["disabled"]
        model = PlatformOffer
        read_only_fields = fields

    def update(self, instance, validated_data):
        instance.disabled = True
        instance.save()
        return instance
    

##ADMIN
class AdminOfferCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferCategory
        fields = '__all__'
        read_only_fields = ['category_slug']