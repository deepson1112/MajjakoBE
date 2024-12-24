from rest_framework.serializers import ModelSerializer
from django.utils import timezone
from menu.models import VendorCategories, VendorDepartment
from retail.models import ProductRequest, ProductsVariationsImage, RefundPolicy, RetailProducts, RetailProductsVariations, RetailVariation, RetailVariationType, generate_sku
from rest_framework import serializers
from django.core.validators import URLValidator
from django.db.models import Q

from retail_marketplace.serializers import PlatformOfferForCartSerializer, RetailGetOneFreeOfferForCartSerializer, RetailProductsVariationsDetailSerializer, RetailSaveOnItemsOfferForCartSerializer, RetailStoreOfferForCartSerializer, calculate_discount
from retail_offers.models import PlatformOffer, RetailGetOneFreeOffer, RetailSaveOnItemsDiscountPercentage, RetailSaveOnItemsOffer, RetailStoreOffer, VendorPlatformOffer
from retail_review.models import Review
from vendor.models import Vendor


class RetailProductsImage(ModelSerializer):
    class Meta:
        fields = ["default_image"]
        model = RetailProducts

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image'] = data['default_image']
        return data

class RetailVariationSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = RetailVariation
        read_only_fields = ['created_date','updated_date']


class RetailVariationTypeSerializer(ModelSerializer):
    variation = RetailVariationSerializer(many=True, required = False)
    class Meta:
        fields = "__all__"
        model = RetailVariationType
        read_only_fields = ['created_date','updated_date']

    def create(self, validated_data):
        variations = validated_data.pop("variations","")
        validated_data['created_date'] = timezone.now()
        validated_data['updated_date'] = timezone.now()
        data =  super().create(validated_data)
        for variation in variations:
            RetailVariation.objects.create(
                **variations,
                variation_type = data,
                created_date = timezone.now(),
                updated_date = timezone.now()
            )
        return data
    
    def update(self, instance, validated_data):
        variations = validated_data.pop("variations","")
        for variation in variations:
            RetailVariation.objects.create(
                **variations,
                variation_type = instance,
                created_date = timezone.now(),
                updated_date = timezone.now()
            )
        return super().update(instance, validated_data)
            

class ProductsVariationsImageSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ProductsVariationsImage
        read_only_fields = ['variations','created_date']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['vendor'] = request.user.user
        return super().create(validated_data)

from rest_framework import serializers

class RetailProductSerializer(ModelSerializer):
    class Meta:
        model = RetailProducts
        fields ="__all__"



class RetailProductsVariationsSerializer(ModelSerializer):
    variations_image = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProductsVariationsImage.objects.all(), write_only=True
    )

    product_detail = serializers.SerializerMethodField()

    def get_product_detail(self, obj):
        serializer = RetailProductSerializer(obj.product).data
        return {
            "id":serializer['id'],
            "product_name":serializer['name'],
            "description":serializer['description'],
            "sub_category":serializer['sub_category'],
            "disabled":serializer['disabled']
        }

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
    
    def create(self, validated_data):
        validated_data['sku']= generate_sku(validated_data['sku'], self.context.get('request').user.user.id)
        validated_data['created_date'] = timezone.now()
        validated_data['updated_date'] = timezone.now()
        variations_image_data = validated_data.pop('variations_image', [])
        data =  super().create(validated_data)

        if variations_image_data:
            data.variations_image.set(variations_image_data)

        return data
    
    def update(self, instance, validated_data):
        variations_image_data = validated_data.pop('variations_image',"")
        variation = validated_data.pop('variation', '')

        if variation:
            instance.variation.clear()
            instance.variation.set(variation)
            
        if variations_image_data:
            instance.variations_image.clear()
            # for image_data in variations_image_data:
            if variations_image_data:
                # image_instance = ProductsVariationsImage.objects.create(**image_data)
                instance.variations_image.set(variations_image_data)
                
        instance.save()
        return super().update(instance, validated_data)
    
class CreateMultipleProductVariationsSerializer(serializers.Serializer):
    products = RetailProductsVariationsSerializer(many=True)

    def to_representation(self, instance):
        return instance
    
    def create(self, validated_data):
        items = validated_data['products']
        return_items = []
        for item in items:
            item['sku']= generate_sku(item['sku'], self.context.get('request').user.user.id)
            item['created_date'] = timezone.now()
            item['updated_date'] = timezone.now()
            variations_image = item.pop('variations_image',"")
            variation = item.pop('variation',"")
            data = RetailProductsVariations.objects.create(
                **item
            )

            data.variation.set(variation)

            data.variations_image.set(variations_image)

            data.save()


            return_items.append(RetailProductsVariationsSerializer(data, many=False, context={"request":self.context.get("request")}).data)
        return {
            
            "products":return_items
            }

from django.db.models import Max, Min

class RefundPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundPolicy
        fields = "__all__"

class VendorRetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class RetailProductsSerializer(ModelSerializer):
    products_variations = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = RetailProducts
        read_only_fields = ['created_date','updated_date','product_unique_id', 'vendor']

    def get_price_range(self, instance):
        prices = instance.products_variations.all().aggregate(Max('price'), Min('price'))

        return {
            'max_price': prices['price__max'],
            'min_price': prices['price__min']
        }

    def to_representation(self, instance):
        data =super().to_representation(instance)

        variations_data = []
        
        #TODO:To make the query shorter
        variation_types =  RetailVariationType.objects.filter(
                variation__products__product=instance,
                disabled=False
            ).distinct()
        
        for each_type in variation_types:
            available_variations = []

            #TODO: Need to optimize this query
            variations = RetailVariation.objects.filter(
                products__product=instance,
                variation_type=each_type,
                disabled=False
            ).distinct()

            for variation in variations:
                product_variation = RetailProductsVariations.objects.filter(
                    product=instance,
                    variation=variation,
                    disabled=False
                ).first()

                available_variations.append({
                    "id": variation.id,
                    "name": variation.name,
                    "variation_image":  [
                        image_data['image'] for image_data in ProductsVariationsImageSerializer(
                            product_variation.variations_image.all(),
                            many=True,
                            context=self.context
                        ).data
                    ]if product_variation and product_variation.variations_image.all().exists() else [RetailProductsImage(instance, many=False, context={"request":self.context.get('request')}).data]
                })

            # Append the data for the current variation type
            variations_data.append({
                "id": each_type.id,
                "name": each_type.name,
                "available_variations": available_variations
            })

        data['variations_data'] = variations_data

        data['refund_policies'] = instance.refund_policies.all().values()
        data['vendor'] = {
            "id" :instance.vendor.id,
            "vendor_name" : instance.vendor.vendor_name,
            "vendor_location" :  instance.vendor.vendor_location
        }

        data['category'] = {
            "id" : instance.category.id,
            "category_name": instance.category.department_name
        }

        data['sub_category'] = {
            "id" : instance.sub_category.id,
            "sub_category_name" : instance.sub_category.category_name
        }
        
        return data

    def get_products_variations(self, instance):
        request = self.context.get('request')
        a = dict(request.query_params)
        retail_product_variations_with_offers = []
        
        filter = list(map(int, a.get('variations', "")))
        if filter:
            retail_product_variations = instance.products_variations.filter(
                variation__id__in=filter,
                disabled = False
            ).distinct()
        else:
            retail_product_variations = instance.products_variations.filter(disabled=False)

        # serialized_data = RetailProductsVariationsSerializer(
        #     retail_product_variations,
        #     many=True,
        #     read_only=True,
        #     context={"request": self.context.get("request")}
        # ).data

        for retail_product_variation in retail_product_variations:
            retail_product_variation_with_offer = RetailProductsVariationsDetailSerializer(
                retail_product_variation,
                context={"request":request}
            ).data

            if retail_product_variation_with_offer["discount"]:
                discount_amount = 0
                discounted_amount = 0
                discount_percentage = 0
                actual_price = retail_product_variation_with_offer["price"]
                discount_type =  retail_product_variation_with_offer["discount"]["offer_type"]

                if discount_type == "SAVE ON ITEMS":
                    discount_percentage = retail_product_variation_with_offer["discount"]["discount_percentages"]

                if discount_type == "STORE OFFER":
                    discount_percentage = retail_product_variation_with_offer["discount"]["discount_percentages"]
                
                if discount_type == "PLATFORM OFFER":
                    discount_percentage = retail_product_variation_with_offer["discount"]["discount_percentages"]
                
                if discount_percentage:
                    discount_amount = float(discount_percentage/100) * float(actual_price)
                    discounted_amount = float(actual_price) - discount_amount

                retail_product_variation_with_offer["discount_amount"] = round(discount_amount, 2)
                retail_product_variation_with_offer["discounted_amount"] = round(discounted_amount, 2)

            retail_product_variations_with_offers.append(retail_product_variation_with_offer)

        return retail_product_variations_with_offers
    
    def create(self, validated_data):
        validated_data['created_date'] = timezone.now()
        validated_data['updated_date'] = timezone.now()
        validated_data['vendor'] = self.context.get('request').user.user

        refund_policies = validated_data.pop('refund_policies', '')
        
        data =  super().create(validated_data)

        if refund_policies:
            data.refund_policies.set(refund_policies)

        return data

    def update(self, instance, validated_data):
        refund_policies = validated_data.pop('refund_policies', '')

        if refund_policies:
            instance.refund_policies.clear()
            instance.refund_policies.set(refund_policies)

        return super().update(instance, validated_data)

class RetailProductListSerializer(ModelSerializer):
    price = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    total_rating = serializers.SerializerMethodField()
    total_review = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    discounted_amount = serializers.SerializerMethodField()

    class Meta:
        fields = ["id", 'name', 'description', 'default_image', 'image_1', 'price', 'sub_category', 'category', 'discount_percentage', 'discounted_amount', 'total_rating', 'total_review', 'delivery_time','average_rating', 'discount_amount']
        model = RetailProducts
    
    def get_average_rating(self, obj):
        reviews = Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True)
        total_ratings = 0
        avg = 0
        for review in reviews:
            if review.rating:
                total_ratings += review.rating
        total_reviews = reviews.count()
        if total_ratings and total_reviews:
            avg = total_ratings/total_reviews
        return avg
    
    def get_total_rating(self, obj):
        reviews = Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True)
        total_ratings = 0
        for review in reviews:
            if review.rating:
                total_ratings += review.rating
        return total_ratings

    def get_total_review(self, obj):
        reviews = Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True)
        return reviews.count()
    
    def get_price(self, instance):
        product_variation = instance.products_variations.filter(disabled=False).first()
        price = RetailProductsVariationsSerializer(product_variation).data['price']
        return price
    
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
    
    def get_discount_percentage(self, obj):
        discount_percentage = 0
        if obj.products_variations.all():
            variations = obj.products_variations.all()
            for variation in variations:
                discount = self.get_discount(instance=variation)
                if discount and 'discount_percentages' in  discount:
                    discount_percentage = max(discount['discount_percentages'],discount_percentage ) 
            return discount_percentage
        return None
    
    def get_discount_amount(self, obj):
        discount_amount = 0
        price = self.get_price(instance=obj)
        discount_percentage = self.get_discount_percentage(obj)
        if discount_percentage and discount_percentage != 0:
            discount_amount = float(discount_percentage/100) *  float(price)
        return discount_amount
    
    def get_discounted_amount(self, obj):
        discount_amount = self.get_discount_amount(obj)
        price = self.get_price(instance=obj)
        discounted_amount = 0
        if discount_amount:
            discounted_amount = float(price) - discount_amount
            discounted_amount = round(discounted_amount, 2)
        return discounted_amount

class RetailSubCategoriesSerializer(ModelSerializer):
    # retail_products = RetailProductSerializer(many=True)
    class Meta:
        fields = "__all__"
        model = VendorCategories
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['retail_products'] = instance.retail_products.all().values('id') if instance.retail_products.exists() else None

        return data
    

class DetailRetailSubCategoriesSerializer(ModelSerializer):
    num_items = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = VendorCategories
    
    def get_num_items(self, obj):
        items = RetailProducts.objects.filter(sub_category=obj).count()
        return items

class RetailCategoriesSerializer(ModelSerializer):
    vendor_categories = RetailSubCategoriesSerializer(many=True)
    class Meta:
        fields = "__all__"
        model = VendorDepartment


class NestedProductVariationSerializer(ModelSerializer):
    variations_image = serializers.ListField(
        child=serializers.CharField(), write_only=True
    )

    variations_data = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'description', 'variation', 'price', 'sku', 'stock_quantity', 'variations_image', 'variations_data', 'disabled']
        model = RetailProductsVariations
        read_only_fields = ['product', 'created_date','updated_date', 'tax_exclusive_price', 'tax_amount', 'sku']
    
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

    def get_variations_data(self, obj):
        variations_data = []
        for each_type in RetailVariationType.objects.filter(variation__products__product = obj.product).distinct():

            variations_data.append({
                "id":each_type.id,
                "name":each_type.name,
                "available_variations": [{
                    "id":variation.id,
                    "name":variation.name
                } for variation in RetailVariation.objects.filter(products__product = obj.product,variation_type=each_type ).distinct()]
            })
        return variations_data

class NestedProductSerializer(ModelSerializer):
    products_variations = NestedProductVariationSerializer(many=True, write_only=True)
    products_variations_detail = serializers.SerializerMethodField(read_only=True)

    default_image_url = serializers.CharField(max_length=1000, required=False, validators=[URLValidator()])
    image_1_url = serializers.CharField(max_length=1000, required=False, validators=[URLValidator()])
    image_2_url = serializers.CharField(max_length=1000,required=False, validators=[URLValidator()])
    image_3_url = serializers.CharField(max_length=1000, required=False, validators=[URLValidator()])
    image_4_url = serializers.CharField(max_length=1000, required=False, validators=[URLValidator()])

    class Meta:
        fields = "__all__"
        model = RetailProducts
        read_only_fields = ['vendor', 'default_image', 'image_1', 'image_2', 'image_3', 'image_4']
        
    
    def to_representation(self, instance):
        product = super().to_representation(instance)
        product['refund_policies'] = instance.refund_policies.all().values()
        return product
    
    def get_products_variations_detail(self, obj):
        variations = obj.products_variations.filter(disabled=False) if hasattr(obj, 'products_variations') else []
        serializer = NestedProductVariationSerializer(variations, many=True, context={"request":self.context.get('request')}) 
        return serializer.data
        
    def create(self, validated_data):
        validated_data['vendor'] = self.context.get('request').user.user
        base_url = "http://dev.majjakodeals.com/media/"

        def strip_base_url(url):
            if url and url.startswith(base_url):
                return url[len(base_url):]
            return url

        validated_data['default_image'] = strip_base_url(validated_data.pop('default_image_url', None))
        validated_data['image_1'] = strip_base_url(validated_data.pop('image_1_url', None))
        validated_data['image_2'] = strip_base_url(validated_data.pop('image_2_url', None))
        validated_data['image_3'] = strip_base_url(validated_data.pop('image_3_url', None))
        validated_data['image_4'] = strip_base_url(validated_data.pop('image_4_url', None))

        products_variations = validated_data.pop('products_variations', [])

        refund_policies = validated_data.pop('refund_policies', [])

        product = RetailProducts.objects.create(**validated_data)

        if refund_policies:
            product.refund_policies.set(refund_policies)

        for products_variation in products_variations:
            sku = generate_sku(products_variation.get('sku', ""), self.context.get('request').user.user.id)
            products_variation['sku'] = sku
            products_variation['product'] = product
            variations_data = products_variation.pop('variation', [])
            variations_image_data = products_variation.pop('variations_image', [])

            product_variation = RetailProductsVariations.objects.create(**products_variation)

            if variations_image_data:
                image_urls = [strip_base_url(item) for item in variations_image_data]
                images = ProductsVariationsImage.objects.filter(image__in=image_urls)
                product_variation.variations_image.set(images)

            if variations_data:
                product_variation.variation.set(variations_data)
        
        if all([product.name, product.description, product.category, product.sub_category, product.refund_policies.exists(),product.default_image]):
            for product_variation in product.products_variations.all():
                if all([product_variation.price, product_variation.sku, product_variation.stock_quantity]):
                    product.is_complete = True
                    product.save()

        return product
    
    def update(self, instance, validated_data):
        base_url = "http://dev.majjakodeals.com/media/"

        def strip_base_url(url):
            if url and url.startswith(base_url):
                return url[len(base_url):]
            return url

        validated_data['default_image'] = strip_base_url(validated_data.pop('default_image_url', None))
        validated_data['image_1'] = strip_base_url(validated_data.pop('image_1_url', None))
        validated_data['image_2'] = strip_base_url(validated_data.pop('image_2_url', None))
        validated_data['image_3'] = strip_base_url(validated_data.pop('image_3_url', None))
        validated_data['image_4'] = strip_base_url(validated_data.pop('image_4_url', None))

        refund_policies = validated_data.pop('refund_policies', [])
        if refund_policies:
            instance.refund_policies.clear()
            instance.refund_policies.set(refund_policies)
        
        # Handle product variations
        products_variations_data = validated_data.pop('products_variations', [])
        existing_variations = {v.sku: v for v in instance.products_variations.all()}

        for variation_data in products_variations_data:
            # Extract nested data
            sku = variation_data.get('sku', None)
            variations_image_data = variation_data.pop('variations_image', [])
            variations_data = variation_data.pop('variation', [])

            # Update existing variation or create a new one
            if sku in existing_variations:
                product_variation = existing_variations.pop(sku)
                for attr, value in variation_data.items():
                    setattr(product_variation, attr, value)
                product_variation.save()
            else:
                # Generate SKU for new variations
                sku = generate_sku(variation_data.get('sku', ""), self.context.get('request').user.user.id)
                variation_data['sku'] = sku
                variation_data['product'] = instance
                product_variation = RetailProductsVariations.objects.create(**variation_data)

            # Handle variation images
            if variations_image_data:
                image_urls = [strip_base_url(img_url) for img_url in variations_image_data if img_url]
                if image_urls:
                    images = ProductsVariationsImage.objects.filter(image__in=image_urls)
                    product_variation.variations_image.set(images)

            # Handle variation data (e.g., attributes)
            if variations_data:
                product_variation.variation.clear()
                product_variation.variation.set(variations_data)

        # Delete remaining variations not in the request
        if existing_variations:
            product_variations = RetailProductsVariations.objects.filter(id__in=[v.id for v in existing_variations.values()])
            for product_variation in product_variations:
                product_variation.variation.clear()
            product_variations.update(disabled=True)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        
        if all([instance.name, instance.description, instance.category, instance.sub_category, instance.refund_policies.exists(),instance.default_image]):
            for product_variation in instance.products_variations.all():
                if all([product_variation.price, product_variation.sku, product_variation.stock_quantity]):
                    instance.is_complete = True
                    instance.save()

        return instance

#ADMIN

class AdminRetailVariationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailVariationType
        fields = "__all__"

class AdminRetailVariationSerializer(ModelSerializer):
    variation_type = serializers.PrimaryKeyRelatedField(queryset=RetailVariationType.objects.all(), write_only=True)
    variation_type_detail = AdminRetailVariationTypeSerializer(source='variation_type', read_only=True)
    class Meta:
        fields = "__all__"
        model = RetailVariation
        read_only_fields = ['created_date','updated_date']

class AdminNestedProductSerializer(ModelSerializer):
    products_variations = NestedProductVariationSerializer(many=True, write_only=True)
    products_variations_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = "__all__"
        model = RetailProducts
    
    def to_representation(self, instance):
        product = super().to_representation(instance)
        product['refund_policies'] = RefundPolicySerializer(instance.refund_policies.all(), many=True).data
        return product
    
    def get_products_variations_detail(self, obj):
        variations = obj.products_variations.all() if hasattr(obj, 'products_variations') else []
        serializer = NestedProductVariationSerializer(variations, many=True, context={"request":self.context.get('request')}) 
        return serializer.data
        
    def create(self, validated_data):
        products_variations = validated_data.pop('products_variations', [])

        refund_policies = validated_data.pop('refund_policies', [])

        product = RetailProducts.objects.create(**validated_data)

        if refund_policies:
            product.refund_policies.set(refund_policies)

        for products_variation in products_variations:
            sku = generate_sku(products_variation['sku'], self.context.get('request').user.user.id)
            products_variation['sku'] = sku
            products_variation['product'] = product
            variations_data = products_variation.pop('variation', [])
            variations_image_data = products_variation.pop('variations_image', [])

            product_variation = RetailProductsVariations.objects.create(**products_variation)

            if variations_image_data:
                product_variation.variations_image.set(variations_image_data)

            if variations_data:
                product_variation.variation.set(variations_data)

        return product
    
    def update(self, instance, validated_data):
        refund_policies = validated_data.get('refund_policies', [])

        if refund_policies:
            instance.refund_policies.clear()
            instance.refund_policies.set(refund_policies)

        products_variations = validated_data.pop('products_variations', [])
        for variation_data in products_variations:
            product_variation = RetailProductsVariations.objects.filter(id=variation_data.get('id')).first()
            variations_image_data = variation_data.pop('variations_image', [])
            variations_data = variation_data.pop('variation', [])

            if product_variation:
                for attr, value in variation_data.items():
                    setattr(product_variation, attr, value)
                product_variation.save()
            else:
                sku = generate_sku(variation_data['sku'], self.context.get('request').user.user.id)
                variation_data['sku'] = sku
                variation_data['product'] = instance
                product_variation = RetailProductsVariations.objects.create(**variation_data)
            
            if variations_image_data:
                product_variation.variations_image.set(variations_image_data)
            
            if variations_data:
                product_variation.variation.set(variations_data)
        return super().update(instance, validated_data)

class ProductRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRequest
        fields = "__all__"
        read_only_fields = ["first_name", "last_name", "email"]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['first_name'] = request.user.first_name
        validated_data['last_name'] = request.user.last_name
        validated_data['email'] = request.user.email

        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorDepartment
        fields = "__all__"

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorCategories
        fields = "__all__"


class EditProductImage(serializers.ModelSerializer):
    class Meta:
        fields = ["default_image", "image_1", "image_2", "image_3", "image_4"]
        model = RetailProducts

class DetailProductsVariationsImageEditProductSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = ProductsVariationsImage
        read_only_fields = ['variations','created_date']

class RetailProductsVariationEditProductSerializer(serializers.ModelSerializer):
    tax_percentage = serializers.SerializerMethodField()
    class Meta:
        model = RetailProductsVariations
        fields = ["id", "product", "variation", "price", "description", "specifications", "stock_quantity", "sku", "tax_percentage","created_date", "updated_date", "variations_image", "disabled"]

    def get_tax_percentage(self, instance):
        if instance.product.tax_rate != 0:
            tax_rate = instance.product.tax_rate
        elif instance.product.sub_category.tax_rate != 0:
            tax_rate = instance.product.sub_category.tax_rate
        elif instance.product.category.tax_rate != 0:
            tax_rate = instance.product.category.tax_rate
        else:
            tax_rate = 0

        return tax_rate
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['variation'] = [{"id":each_product.id, "variation_type":each_product.variation_type.id, "variation_name":each_product.name,"variation_type_name":each_product.variation_type.name} 
                             for each_product in instance.variation.all()
                             ]
        data['variations_image'] = DetailProductsVariationsImageEditProductSerializer(
                instance.variations_image.all(),
                many=True,
                context=self.context
            ).data if instance.variations_image.all() else [EditProductImage(instance.product, many=False, context={"request":self.context.get('request')}).data]

        return data
    
class EditProductSerializer(serializers.ModelSerializer):
    products_variations = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = RetailProducts
        read_only_fields = ['created_date','updated_date','product_unique_id', 'vendor']

    def get_price_range(self, instance):
        prices = instance.products_variations.all().aggregate(Max('price'), Min('price'))
        return {
            'max_price': prices['price__max'],
            'min_price': prices['price__min']
        }

    def to_representation(self, instance):
        data =super().to_representation(instance)

        variations_data = []
        variation_types = RetailVariationType.objects.filter(
                variation__products__product=instance
            ).distinct()
        
        for each_type in variation_types:
            available_variations = []

            variations = RetailVariation.objects.filter(
                products__product=instance,
                variation_type=each_type
            ).distinct()

            for variation in variations:
                product_variation = RetailProductsVariations.objects.filter(
                    product=instance,
                    variation=variation
                ).first()

                available_variations.append({
                    "id": variation.id,
                    "name": variation.name,
                    "variation_image":  [
                        image_data['image'] for image_data in ProductsVariationsImageSerializer(
                            product_variation.variations_image.all(),
                            many=True,
                            context=self.context
                        ).data
                    ]if product_variation and product_variation.variations_image.all().exists() else [RetailProductsImage(instance, many=False, context={"request":self.context.get('request')}).data]
                })

            # Append the data for the current variation type
            variations_data.append({
                "id": each_type.id,
                "name": each_type.name,
                "available_variations": available_variations
            })

        data['variations_data'] = variations_data

        data['refund_policies'] = RefundPolicySerializer(instance.refund_policies.all(), many=True).data
        data['vendor'] = {
            "id" :instance.vendor.id,
            "vendor_name" : VendorRetailSerializer(instance.vendor).data['vendor_name']
        }

        data['category'] = {
            "id" : instance.category.id,
            "category_name": RetailCategoriesSerializer(instance.category).data['department_name']
        }

        data['sub_category'] = {
            "id" : instance.sub_category.id,
            "sub_category_name" : RetailSubCategoriesSerializer(instance.sub_category).data['category_name']
        }
        
        return data

    def get_products_variations(self, instance):
        request = self.context.get('request')
        a = dict(request.query_params)
        try:
            filter = list(map(int, a['variations']))
            retail_product_variations = instance.products_variations.filter(
                variation__id__in=filter
            ).distinct()
        except KeyError:
            retail_product_variations = instance.products_variations.all()

        serialized_data = RetailProductsVariationEditProductSerializer(
            retail_product_variations,
            many=True,
            read_only=True,
            context={"request": self.context.get("request")}
        ).data

        return serialized_data
    