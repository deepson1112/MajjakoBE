from django.db import models

from retail_offers.models import PlatformOffer
from retail_product_display.models import CategoryGroup
from vendor.models import Vendor

# Create your models here.
class HomepageSection(models.Model):
    section_code = models.CharField(max_length=100, unique=True)
    section_name = models.CharField(max_length=100)

    def __str__(self):
        return self.section_code

class HomepageContent(models.Model):
    section_code = models.ForeignKey(HomepageSection, on_delete=models.CASCADE, related_name='content')
    category_group = models.ForeignKey(CategoryGroup,  on_delete=models.CASCADE, related_name='content', null=True, blank=True)
    platform_offer = models.ForeignKey(PlatformOffer, on_delete=models.CASCADE, related_name='content', null=True, blank=True)
    image = models.ImageField(upload_to='homepage-content/', null=True, blank=True)
    title_text = models.CharField(max_length=255, null=True, blank=True)
    button_text = models.CharField(max_length=100, null=True, blank=True)
    hyperlink = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='content', null=True, blank=True)

    def __str__(self):
        return self.section_code.section_code



class AdsSection(models.Model):
    position_code = models.CharField(max_length=100, unique=True)
    ad_name = models.CharField(max_length=100)
    image_height = models.IntegerField(null=True, blank=True)
    image_width = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='ads-section/', null=True, blank=True)
    hyperlink = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.position_code

