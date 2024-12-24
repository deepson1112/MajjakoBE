from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet

from utils.permissions_override import IsSuperAdmin

from .serializers import DeliveryDriverLocationSerializer, DeliveryDriverStatusSerializer, DeliveryDriverSerializer
from .models import DeliveryDriverLocation, DeliveryDriverStatus, DeliveryDriver

# Create your views here.

class DeliveryDriverLocationViewSet(ModelViewSet):
    queryset = DeliveryDriverLocation.objects.all()
    serializer_class = DeliveryDriverLocationSerializer
    permission_classes = [IsSuperAdmin]

class DeliveryDriverStatusViewSet(ModelViewSet):
    queryset = DeliveryDriverStatus.objects.all()
    serializer_class = DeliveryDriverStatusSerializer
    permission_classes = [IsSuperAdmin]

class DeliveryDriverViewSet(ModelViewSet):
    queryset = DeliveryDriver.objects.all()
    serializer_class = DeliveryDriverSerializer