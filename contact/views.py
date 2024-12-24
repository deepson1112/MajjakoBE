from django.shortcuts import render
from rest_framework import viewsets
from retail_orders.views import StandardResultsSetPagination
from utils.mail import send_mail_using_graph
from django.template.loader import render_to_string
from rest_framework.response import Response

from utils.permissions_override import IsSuperAdmin

from .serializer import ContactSerializer
from .models import Contact

# Create your views here.
class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        if response.status_code == 201:
            contact_data = response.data

            mail_subject = 'Thank You for Contacting Us!'
            mail_template = 'contact/contact.html'

            context = {
                "to_email" : contact_data['email'],
                "name" : contact_data['first_name'] + " " + contact_data['last_name'],
            }

            send_mail_using_graph(
                receiver_email=context['to_email'], 
                subject=mail_subject, 
                message_text=render_to_string(mail_template, context)
            )
        return response

class AdminContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.order_by('-created_at')
    serializer_class = ContactSerializer
    http_method_names = ['get']
    permission_classes = [IsSuperAdmin]

    def retrieve(self, request, *args, **kwargs):
        review_instance = self.get_object()
        review_instance.seen = True
        review_instance.save()
        serializer = self.get_serializer(review_instance)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()

        queryset = self.filter_queryset(self.get_queryset())
        unseen_count = queryset.filter(seen=False).count()

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            paginated_response.data['unseen_count'] = unseen_count
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'unseen_count': unseen_count,
            'results': serializer.data
        })