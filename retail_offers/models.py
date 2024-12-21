from django.db import models
from django.utils.text import slugify
import uuid
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from menu.models import VendorCategories
from retail.models import RetailProducts, RetailProductsVariations
from user.models import User
from vendor.models import Vendor

# Create your models here.

class OfferCategory(models.Model):
    products = models.ManyToManyField(RetailProducts, related_name='offer_categories')
    category_name = models.CharField(max_length=255)
    category_slug = models.SlugField()
    category_description = models.TextField(null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='offer_categories', null=True, blank=True)
    active = models.BooleanField(default=True)
    categories_order = models.IntegerField(default=1)
    image = models.ImageField('department/', null=True, blank=True)

    def __str__(self) -> str:
        return self.category_name

    def save(self, **kwargs):
        if not self.category_slug:
            self.category_slug = slugify(self.category_name)
            unique_id = uuid.uuid4().hex[:6]
            self.category_slug = self.category_slug + unique_id

        return super(OfferCategory, self).save(**kwargs)

AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)

class RetailStoreOffer(models.Model):
    offer_name = models.CharField(max_length = 100, null=True)
    discount_percentages = models.FloatField(default=0)
    
    minimum_spend_amount = models.FloatField(default=0)
    maximum_redeem_value = models.FloatField(default=0, null=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')

    discount_banner = models.ImageField(upload_to="reatil_offers_banner/", null=True
                                        )
    active = models.BooleanField(default=True)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE, related_name="store_offers")
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.offer_name


class RetailGetOneFreeOffer(models.Model):
    retail_products = models.ManyToManyField(RetailProducts, related_name='bogo')
    offer_name = models.CharField(max_length = 255, null=True, default="")
    active = models.BooleanField(default=True)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')    
    
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    discount_banner = models.ImageField(upload_to="reatil_offers_banner/", null=True)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE, related_name="get_one_free_offers")
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.offer_name

class RetailSaveOnItemsOffer(models.Model):
    offer_name = models.CharField(max_length = 255, null=True)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')        
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    discount_banner = models.ImageField(upload_to="reatil_offers_banner/", null=True)
    disabled = models.BooleanField(default=False)
    

    def __str__(self) -> str:
        return self.offer_name


class RetailSaveOnItemsDiscountPercentage(models.Model):
    store_offer = models.ForeignKey(RetailSaveOnItemsOffer, on_delete=models.CASCADE, related_name = "offer_items")
    discount_percentages = models.FloatField(default=0)
    retail_product = models.ForeignKey(RetailProducts, null=True, blank=True, on_delete=models.PROTECT, related_name="save_on_items")
    sub_category = models.ForeignKey(VendorCategories, null=True, blank=True, on_delete=models.CASCADE, related_name = 'save_on_items')
    retail_product_variation = models.ForeignKey(RetailProductsVariations, null=True, blank=True, on_delete=models.PROTECT, related_name="save_on_items")
    offer_category = models.ForeignKey(OfferCategory, on_delete=models.CASCADE, null=True, blank=True, related_name="save_on_items")


class RetailCoupon(models.Model):
    COUPON_TYPE = (
        ("Flat Discount","Flat Discount"),
        ("Percentage Off","Percentage Off"),
        ("Delivery Fee  off","Delivery Fee  off")
    )
    
    DISCOUNT_TYPE = (
        ("IN AMOUNT","IN AMOUNT"),
        ("IN PERCENTAGE","IN PERCENTAGE")
    )
   
    discount_amount = models.FloatField(default=0.0)
    discount_type = models.CharField(choices= DISCOUNT_TYPE, help_text = '''
        ("IN AMOUNT","IN AMOUNT"),
        ("IN PERCENTAGE","IN PERCENTAGE")
        ''', 
        default = 'IN AMOUNT'
    )
    discount_percentages = models.FloatField(default = 0.0)
    coupons_title = models.CharField(max_length=255)
    coupon_code = models.CharField(max_length = 25, help_text="max length = 25", unique=True)
    coupon_type = models.CharField(choices = COUPON_TYPE, help_text = '''
        ("Flat Discount","Flat Discount"),
        ("Percentage Off","Percentage Off"),
        ("Delivery Fee  off","Delivery Fee  off")
                                   ''')
    minimum_spend_amount = models.FloatField(default=0.0)
    maximum_redeem_amount = models.FloatField(default=0.0)
    
    limitation_for_user = models.IntegerField()
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    vendor = models.ManyToManyField(Vendor, related_name="retail_coupons")

    coupon_usage_limitation =  models.IntegerField(default=0)
    
    chowchow_coupon = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    usage = models.IntegerField(default=0, null=True)
    disabled = models.BooleanField(default=False)


class RetailLoyaltyPrograms(models.Model):
    program_name = models.CharField(max_length=255)
    program_code = models.CharField(max_length = 255, unique = True, null=True)
    no_of_points = models.IntegerField()
    
    discount_percentages = models.FloatField(default = 0.0)
    
    maximum_redeem_amount = models.FloatField(default=0.0)
    
    minimum_spend_amount = models.FloatField(default=0.0)
    disabled = models.BooleanField(default=False)

class PlatformOffer(models.Model):
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')  
    offer_name = models.CharField(max_length = 255, null=True)      
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    active = models.BooleanField(default=True)
    discount_banner = models.ImageField(upload_to="platform_offers_banner/", null=True)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return self.offer_name
    

#TODO: IS this how the vendor platform offer is to be defined?
class VendorPlatformOffer(models.Model):
    platform_offer = models.ForeignKey(PlatformOffer, on_delete=models.CASCADE, related_name="vendor_platform_offer")
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE, related_name="vendor_platform_offer")
    discount_percentages = models.FloatField()
    retail_product = models.ForeignKey(RetailProducts, null=True, blank=True, on_delete=models.CASCADE, related_name="vendor_platform_offer")
    retail_product_variation = models.ForeignKey(RetailProductsVariations, null=True, blank=True, on_delete=models.CASCADE, related_name="vendor_platform_offer")

    def __str__(self) -> str:
        return self.platform_offer.offer_name


class RetailFreeDelivery(models.Model):
    AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
)
    audience = models.CharField(choices = AUDIENCE, help_text=''' AUDIENCE = (
    ("New Customer", "New Customer"),
    ("All Active Customer", "All Active Customer"),
    ("All Customer", "All Customer"),
    )''')      
    offer_name = models.CharField(max_length = 255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    discount_banner = models.ImageField(upload_to="free_delivery/", null=True, blank=True)
    active = models.BooleanField(default=True)
    minimum_spend_amount = models.FloatField(default=0)
    created_by = models.ForeignKey(User, on_delete = models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        #TODO: Check the validation for Retail free delivery offers creation
        if RetailFreeDelivery.objects.filter(start_date__lte=self.start_date, end_date__gte=self.end_date, active=True).exclude(id=self.id):
            raise ValidationError(_('Free delivery on this time already exists'))

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return self.offer_name
    



