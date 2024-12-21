from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied


from watchlist.models import WatchList
from watchlist.serializers import UserWatchListSerializer
# Create your views here.

class UserWatchListViewSet(viewsets.ModelViewSet):
    queryset = WatchList.objects.all()
    serializer_class = UserWatchListSerializer
    permission_classes = [IsAuthenticated]
    

    def permission_denied(self, request, message=None, code=None):
        if not request.user.is_authenticated:
            raise PermissionDenied(detail="You have to be signed in to use this feature.")
        return super().permission_denied(request, message, code)

    def get_queryset(self):
        return WatchList.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        data = request.data
        product_variation = data['product_variation']

        watchlist = WatchList.objects.filter(user=request.user, product_variation=product_variation)
        if watchlist.exists():
            watchlist.delete()
            return Response({"message":"Removed"})
        return super().create(request, *args, **kwargs)