from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import DeliveryBoundary, DeliveryDriver, DeliveryDriverLocation, DeliveryDriverStatus

class DeliveryDriverLocationSerializer(ModelSerializer):
    class Meta:
        model = DeliveryDriverLocation
        fields = "__all__"

class DeliveryDriverStatusSerializer(ModelSerializer):
    class Meta:
        model = DeliveryDriverStatus
        fields = '__all__'

class DeliveryDriverSerializer(ModelSerializer):
    location = serializers.PrimaryKeyRelatedField(queryset=DeliveryDriverLocation.objects.all(), write_only=True)
    location_detail = DeliveryDriverLocationSerializer(source='location', read_only=True)

    status = serializers.PrimaryKeyRelatedField(queryset=DeliveryDriverStatus.objects.all(), write_only=True)
    status_detail = DeliveryDriverStatusSerializer(source='status', read_only=True)
    class Meta:
        model = DeliveryDriver
        fields = '__all__'

class DeliveryBoundarySerializer(ModelSerializer):
    class Meta:
        model = DeliveryBoundary
        fields = "__all__"