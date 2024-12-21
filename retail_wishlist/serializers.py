from rest_framework import serializers
import uuid

from retail_marketplace.serializers import RetailCartSerializer
from utils.check_delivery_zone import check_delivery_zone
from user.models import User
from user.serializers import UsersSerializer

from .models import RetailWishList, SharedRetailWishlist, UserRetailWishlist

from retail.models import RetailProductsVariations
from retail.serializers import RetailProductsSerializer, RetailProductsVariationsSerializer
from retail_marketplace.models import RetailCart

class RetailWishListSerializer(serializers.ModelSerializer):
    retail_product_variation = serializers.PrimaryKeyRelatedField(
        queryset=RetailProductsVariations.objects.all(), write_only=True
    )
    product_name = serializers.CharField(
        source='retail_product_variation.product.name', read_only=True
    )
    # retail_product_variation_details = RetailProductsVariationsSerializer(
    #     source='retail_product_variation', read_only=True
    # )
    retail_product_variation_details = serializers.SerializerMethodField()

    product_disabled = serializers.SerializerMethodField()

    class Meta:
        model = RetailWishList
        fields = '__all__'
        read_only_fields = ['user', 'wishlist_id', 'product_name', 'retail_product_variation_details']
    
    def get_product_disabled(self, obj):
        if obj.retail_product_variation.disabled == True or obj.retail_product_variation.product.disabled == True:
            return True
        return False
    
    def get_retail_product_variation_details(self, obj):
        retail_product_variation_details = RetailProductsVariationsSerializer(obj.retail_product_variation,  context={"request":self.context.get("request")})
        return retail_product_variation_details.data
    
    def validate(self, attrs):
        user = self.context.get('request').user
        retail_product_variation = attrs.get('retail_product_variation', None)

        if RetailWishList.objects.filter(user=user, retail_product_variation=retail_product_variation, active=True).exists():
            raise serializers.ValidationError({"msg": "Product already exists in wishlist"})

        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        validated_data['wishlist_id'] = uuid.uuid4()
        wishlist = RetailWishList.objects.create(**validated_data)

        user_wishlist = UserRetailWishlist.objects.create(
            user = request.user,
            wishlist = wishlist
        )
        return wishlist

class SharedRetailWishlistSerializer(serializers.ModelSerializer):   
    wishlists = serializers.PrimaryKeyRelatedField(many=True, queryset=RetailWishList.objects.all(), write_only=True)
    # wishlist_details = RetailWishListSerializer(many=True, read_only=True, source='wishlists')

    wishlist_details = serializers.SerializerMethodField()

    # buyer = serializers.SerializerMethodField()

    def get_wishlist_details(self, instance):
        wishlists = instance.wishlists.all()
        wishlist_serializers = RetailWishListSerializer(wishlists, many=True, context={"request": self.context.get("request")}).data

        # Create a mapping from wishlist id to buyer
        wishlist_id_to_buyer = {
            wishlist.id: self.get_buyer(instance, wishlist)
            for wishlist in wishlists
        }

        # Update serializers with buyer information
        for serializer in wishlist_serializers:
            wishlist_id = serializer.get('id')
            serializer['buyer'] = wishlist_id_to_buyer.get(wishlist_id, None)

        return wishlist_serializers
    
    def get_buyer(self, instance, wishlist):
        user = self.context.get('request').user
        cart = RetailCart.objects.filter(shared_wishlist=instance.id, retail_product_variation=wishlist.retail_product_variation.id, orders__isnull=False, orders__payment__isnull=False).first()

        if cart:
            user = User.objects.get(id=cart.user.id)
            user_serializer = UsersSerializer(user).data
            return {
                "user_id": user_serializer['id'],
                "user_first_name": user_serializer['first_name'],
                "user_last_name": user_serializer['last_name'],
                "user_email": user_serializer['email'],
                "quantity": cart.quantity
            }

        return None
    
    class Meta:
        model = SharedRetailWishlist
        fields = '__all__'  
        read_only_fields = ['email'] 

    def create(self, validated_data):
        request = self.context.get('request')

        user_lat = validated_data['latitude']
        user_long = validated_data['longitude']
        delivery_boundary_response = check_delivery_zone(user_lat, user_long)
        if not delivery_boundary_response:
            raise serializers.ValidationError({"message": "Delivery Not Available", "delivery_available":False})

        validated_data['email'] = request.user.email
        wishlists = validated_data.pop('wishlists', None)
        if not wishlists:
            raise serializers.ValidationError({"message": "Wishlist is empty"})
        shared_wishlist = SharedRetailWishlist.objects.create(**validated_data)
        shared_wishlist.wishlists.set(wishlists)
        return shared_wishlist
