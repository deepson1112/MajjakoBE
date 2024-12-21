from django.shortcuts import render
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

from .serializers import CategoryGroupDetailSerializer, CategoryGroupSerializer
from .models import CategoryGroup

# Create your views here.
class CategoryGroupProductDisplayViewSet(viewsets.ModelViewSet):
    queryset = CategoryGroup.objects.all()
    serializer_class = CategoryGroupSerializer
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group_name']

    def list(self, request, *args, **kwargs):
        if request.query_params.get('group_name'):
            try:
                queryset = CategoryGroup.objects.get(group_name=request.query_params.get('group_name'))
            except:
                raise ValidationError({'message':'Group name invalid.'})
            serializer = CategoryGroupSerializer(queryset).data
            return Response(serializer, status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)

class CategoryGroupViewSet(viewsets.ModelViewSet):
    queryset = CategoryGroup.objects.all()
    serializer_class = CategoryGroupDetailSerializer
    http_method_names = ['get']