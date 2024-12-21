from rest_framework import serializers
from urllib.parse import urljoin

from watchlist.models import WatchList

from dvls import settings
domain = settings.DOMAIN

class UserWatchListSerializer(serializers.ModelSerializer):
    product_disabled = serializers.SerializerMethodField()

    class Meta:
        model = WatchList
        fields = "__all__"
        read_only_fields = ['user']

    def get_product_disabled(self, obj):
        if obj.product_variation.disabled == True or obj.product_variation.product.disabled == True:
            return True
        return False
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        data['product_variation'] = {
            'id' : instance.product_variation.id,
            'product_name' : instance.product_variation.product.name,
            'sku' : instance.product_variation.sku,
            'price' : instance.product_variation.price,
            'product_image' :   request.build_absolute_uri(instance.product_variation.product.default_image.url)if instance.product_variation.product.default_image else None
        }
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)