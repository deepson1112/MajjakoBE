from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from .serializers import HomepageSectionSerializer, AdsSectionSerializer
from .models import HomepageSection, AdsSection

# Create your views here.
class HomepageContentViewSet(viewsets.ModelViewSet):
    queryset = HomepageSection.objects.all()
    serializer_class = HomepageSectionSerializer
    filter_backends = [ SearchFilter ]
    search_fields = ['section_code']


class AdsSectionViewSet(viewsets.ModelViewSet):
    queryset = AdsSection.objects.all()
    serializer_class = AdsSectionSerializer
    filter_backends = [ SearchFilter ]
    search_fields = ['position_code']

    def get_queryset(self):
        queryset = AdsSection.objects.all()
        return queryset

