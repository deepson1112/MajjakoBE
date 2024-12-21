from rest_framework import serializers

from menu.models import VendorCategories
from retail_offers.models import PlatformOffer
from retail_product_display.models import CategoryGroup
from vendor.models import Vendor

from .models import HomepageContent, HomepageSection, AdsSection

class CategoryGroupsDetail(serializers.ModelSerializer):
    class Meta:
        model = CategoryGroup
        fields = '__all__'

class DetailPlatformOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformOffer
        fields = '__all__'

class VendorDetailContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"

class HomepageContentSerializer(serializers.ModelSerializer):
    category_group = serializers.PrimaryKeyRelatedField(queryset=VendorCategories.objects.all(), write_only=True)
    category_group_detail = CategoryGroupsDetail(source='category_group', read_only=True)

    platform_offer = DetailPlatformOfferSerializer()
    vendor = VendorDetailContentSerializer()

    class Meta:
        model = HomepageContent
        fields = "__all__"

class HomepageSectionSerializer(serializers.ModelSerializer):
    content = HomepageContentSerializer(many=True)
    class Meta:
        model = HomepageSection
        fields = "__all__"


class AdsSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdsSection
        fields = "__all__"