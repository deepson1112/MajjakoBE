from rest_framework.serializers import ModelSerializer
from django.utils import timezone
from menu.models import FoodItem


class RetailSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = FoodItem
        read_only_fields = ['vendor','created_at','updated_at']

    def create(self, validated_data):
        validated_data['vendor'] = self.context.get('request').user.user
        validated_data['created_at'] = timezone.now()
        validated_data['updated_at'] = timezone.now()
        return super().create(validated_data)
    

    def update(self, instance, validated_data):
        validated_data['updated_at'] = timezone.now()
        return super().update(instance, validated_data)

