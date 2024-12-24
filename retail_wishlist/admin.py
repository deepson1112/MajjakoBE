from django.contrib import admin

from retail_wishlist.models import RetailWishList, SharedRetailWishlist, UserRetailWishlist

# Register your models here.
admin.site.register(RetailWishList)
admin.site.register(SharedRetailWishlist)
admin.site.register(UserRetailWishlist)