from django.db import models

from retail_orders.models import OrderedProduct
from user.models import User

# Create your models here.

class Review(models.Model):
    ordered_product = models.ForeignKey(OrderedProduct, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    image_1 = models.ImageField(upload_to='review-image/', null=True, blank=True)
    image_2 = models.ImageField(upload_to='review-image/', null=True, blank=True)
    image_3 = models.ImageField(upload_to='review-image/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    reply = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"Review of {self.ordered_product.product_variation.product.name} by {self.user.username}"