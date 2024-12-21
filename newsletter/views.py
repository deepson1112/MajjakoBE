from django.shortcuts import render
from rest_framework import viewsets

from newsletter.models import Newsletter
from newsletter.serializer import NewsletterSerializer

from rest_framework.permissions import IsAuthenticated
from utils.permissions_override import IsVendor, IsSuperAdmin

# Create your views here.
class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    # permission_classes = [IsAuthenticated]


#admin can see all the newsletters get request
class AdminNewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    search_fields = ['email']
    http_method_names = ['get']

    def get_queryset(self):
        return Newsletter.objects.all()



