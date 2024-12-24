from rest_framework import serializers
from retail.models import RetailProducts
from retail_review.models import Review


class UserReviewSerializer(serializers.ModelSerializer):
    vendor_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ['user']
    
    def get_vendor_name(self, obj):
        vendor_name = obj.ordered_product.vendor_order.vendor.vendor_name
        return vendor_name
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get('request')

        data['ordered_product'] = {
            "ordered_product_id" : instance.ordered_product.id,
            "product_id" : instance.ordered_product.product_variation.product.id,
            "product_name" : instance.ordered_product.product_variation.product.name,
        }

        data['user'] = {
            "id": instance.user.id,
            "first_name" : instance.user.first_name,
            "last_name" : instance.user.last_name,
            "user_name" : instance.user.username,
            "image":  request.build_absolute_uri(instance.user.user_profile.profile_picture.url) if instance.user.user_profile.profile_picture else None
        }
        return data
    
    def create(self, validated_data):
        request = self.context.get("request")

        if Review.objects.filter(user=request.user, ordered_product=validated_data['ordered_product']).exists():
            raise serializers.ValidationError({'message':'Review exists.'})

        validated_data['user'] = request.user
        review = super().create(validated_data)
        return review

class AverageReviewSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    total_rating = serializers.SerializerMethodField()
    total_review = serializers.SerializerMethodField()

    class Meta:
        model = RetailProducts
        fields = ["id", "name", "description", "default_image", "total_review", "total_rating", "average_rating", "rating"]
    
    def get_average_rating(self, obj):
        reviews = Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True)
        total_ratings = 0
        avg = 0
        for review in reviews:
            total_ratings += review.rating
        total_reviews = reviews.count()
        if total_ratings and total_reviews:
            avg = total_ratings/total_reviews
        return avg

    def get_rating(self, obj):
        return {
            str(rating): Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True, rating=rating).count()
            for rating in range(1, 6)
        }
    
    def get_total_rating(self, obj):
        reviews = Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True)
        total_ratings = 0
        for review in reviews:
            total_ratings += review.rating
        return total_ratings
    
    def get_total_review(self, obj):
        reviews = Review.objects.filter(ordered_product__product_variation__product=obj.id, is_approved=True)
        return reviews.count()