from django.db import models

from retail.models import RetailProductsVariations
from user.models import User

# Create your models here.
class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    product_variation = models.ForeignKey(RetailProductsVariations, on_delete=models.CASCADE, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.user.id)