from django.shortcuts import render

from rest_framework import viewsets

from django.http import HttpResponse
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError, PermissionDenied

from retail_marketplace.models import RetailCart
from user.models import User

from .models import RetailWishList, SharedRetailWishlist, UserRetailWishlist
from .serializers import RetailWishListSerializer, SharedRetailWishlistSerializer

from rest_framework.permissions import IsAuthenticated


# Create your views here.

def get_buyer_data(shared_wishlist, wishlist):
    cart = RetailCart.objects.filter(
        shared_wishlist=shared_wishlist.id, 
        retail_product_variation=wishlist.retail_product_variation.id, 
        orders__isnull=False, 
        orders__payment__isnull=False
    ).first()
    
    if cart:
        return True
    return None

class RetailWishListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = RetailWishList.objects.filter(active=True)
    serializer_class = RetailWishListSerializer

    def permission_denied(self, request, message=None, code=None):
        if not request.user.is_authenticated:
            raise PermissionDenied(detail="You have to be signed in to use this feature.")
        return super().permission_denied(request, message, code)

    def get_queryset(self):
        return RetailWishList.objects.filter(user=self.request.user).filter(active=True).order_by('-created_at')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

class SharedRetailWishlistViewSet(viewsets.ModelViewSet):
    queryset = SharedRetailWishlist.objects.all()
    serializer_class = SharedRetailWishlistSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['uuid']

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid", "")
        if uuid:
            return SharedRetailWishlist.objects.all()
        
        buyer = self.request.query_params.get("buyer", "")
        if buyer == "True":
            shared_wishlists = SharedRetailWishlist.objects.filter(wishlists__user=self.request.user).distinct()
            filtered_shared_wishlists = []
            for shared_wishlist in shared_wishlists:
                has_all_buyers = True
                wishlists = shared_wishlist.wishlists.all()
                for wishlist in wishlists:
                    buyer_data = get_buyer_data(shared_wishlist, wishlist)
                    if not buyer_data:
                        has_all_buyers = False
                        break

                if has_all_buyers:
                        filtered_shared_wishlists.append(shared_wishlist.id)

            return SharedRetailWishlist.objects.filter(id__in=filtered_shared_wishlists)
        
        if buyer == "False":
            shared_wishlists = SharedRetailWishlist.objects.filter(wishlists__user=self.request.user).distinct()
            filtered_shared_wishlists = []

            for shared_wishlist in shared_wishlists:
                has_no_buyers = False
                for wishlist in shared_wishlist.wishlists.all():
                    buyer_data = get_buyer_data(shared_wishlist, wishlist)
                    if not buyer_data:
                        has_no_buyers = True
                        break

                if has_no_buyers:
                    filtered_shared_wishlists.append(shared_wishlist.id)

            return SharedRetailWishlist.objects.filter(id__in=filtered_shared_wishlists)

        return SharedRetailWishlist.objects.filter(wishlists__user=self.request.user).distinct()

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

@api_view(['GET'])
def user_wishlist(request):
    if not request.user.is_authenticated:
        return Response(
            {"message": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    user = request.user
    wishlists = RetailWishList.objects.filter(user=user).filter(active=True)
    product_lists =[]
    if wishlists:
        for wishlist in wishlists:
            product_lists.append(wishlist.retail_product_variation.id)
    return Response({"product_variation": product_lists})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated]) 
def delete_product_wislist(request, variation_id):
    try:
        wishlist_item = RetailWishList.objects.filter(retail_product_variation=variation_id, active=True).first()
        wishlist_item.active = False
        wishlist_item.save()
        
        return Response(status=204)
    except RetailWishList.DoesNotExist:
        return Response({"message": "Wishlist item not found"}, status=404)