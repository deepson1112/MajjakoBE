from rest_framework import serializers

from menu.models import VendorCategories
from retail.models import RetailProducts, RetailProductsVariations

from .models import CategoryGroup

class DetailRetailProductsVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailProductsVariations
        fields = "__all__"

class DetailRetailProductListSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        fields = ["id", 'name', 'description', 'default_image', 'image_1', 'price', 'sub_category']
        model = RetailProducts
    
    def get_price(self, instance):
        product_variation = instance.products_variations.first()
        price = DetailRetailProductsVariationSerializer(product_variation).data['price']
        return price

class DetailCategorySerializer(serializers.ModelSerializer):
    retail_products = DetailRetailProductListSerializer(many=True)
    class Meta:
        model = VendorCategories
        fields = "__all__"
        
class CategoryGroupSerializer(serializers.ModelSerializer):
    category = DetailCategorySerializer(many=True)
    class Meta:
        model = CategoryGroup
        fields = "__all__"

class CategoryGroupDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryGroup
        fields = "__all__"