from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from utils.permissions_override import IsVendor
from vendor.models import FAQS, Offerings, OpeningHour, Vendor, VendorHourTimelines
from vendor.serializers import FAQSSerializer, OfferingsSerializer, OpeningHourSerializer, VendorSerializer, VendorHoursSerializer
from django_filters.rest_framework import DjangoFilterBackend

class VendorViews(ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vendor_type']


class OpeningHourViews(ModelViewSet):
    queryset = OpeningHour.objects.all()
    serializer_class = OpeningHourSerializer


class VendorHoursViews(ModelViewSet):
    queryset = VendorHourTimelines.objects.all()
    serializer_class = VendorHoursSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        user = self.request.user
        return VendorHourTimelines.objects.filter(vendor__user = user)


class OfferingsViewSet(ModelViewSet):
    queryset = Offerings.objects.all()
    serializer_class = OfferingsSerializer
    http_method_names = ["get"]



class FAQSViewSet(ModelViewSet):
    http_method_names = ['get']
    serializer_class = FAQSSerializer
    queryset = FAQS.objects.filter(active=True).order_by('order')