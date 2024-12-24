from django.db import models

from menu.models import VendorCategories

class CategoryGroup(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    category = models.ManyToManyField(VendorCategories)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.group_name
