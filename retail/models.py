from django.db import models

from menu.models import VendorCategories, VendorDepartment
import uuid

from user.models import User
from vendor.models import Vendor
# Create your models here.

class RefundPolicy(models.Model):
    policy = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.policy

class RetailVariationType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

class RetailVariation(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    variation_type = models.ForeignKey(RetailVariationType, on_delete = models.CASCADE, related_name = "variation") 
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

DELIVERY_TIME = (
    ("same day","same day"),
    ("1-2 days","1-2 days"),
    ( "3-5 days", "3-5 days"),
    ( "5-7 days", "5-7 days")
)

class RetailProducts(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(VendorDepartment,on_delete=models.CASCADE, related_name = 'retail_products')
    sub_category = models.ForeignKey(VendorCategories,on_delete=models.CASCADE, related_name = 'retail_products')
    discountable = models.BooleanField(default=False)
    age_restriction = models.BooleanField(default=False)
    product_unique_id = models.UUIDField(default=uuid.uuid4)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_retails',null=True)
    default_image = models.ImageField( upload_to= 'retail_products/', null=True)
    image_1 = models.ImageField(upload_to='retail_products/', null=True, blank=True)
    image_2 = models.ImageField(upload_to= 'retail_products/', null=True, blank=True)
    image_3 = models.ImageField(upload_to= 'retail_products/', null=True, blank=True)
    image_4 = models.ImageField(upload_to= 'retail_products/', null=True, blank=True)

    # price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00)

    created_date = models.DateTimeField(auto_now_add=True,null=True)
    updated_date = models.DateTimeField(auto_now_add=True,null=True)

    tax_rate = models.FloatField(default=0.0)
    tax_exempt = models.BooleanField(default=False)

    refund_policies = models.ManyToManyField(RefundPolicy)
    disabled = models.BooleanField(default=False)

    is_complete = models.BooleanField(default=False)

    delivery_time = models.CharField(max_length=50, choices=DELIVERY_TIME, default="same day", null=True, blank=True)

    special_request = models.BooleanField(default=False, null=True, blank=True)

    # def get_refund_policy(self):
    #     for each_data in self.refund_policies:
    #         return{

    #         }

    def __str__(self) -> str:
        return self.name

class ProductsVariationsImage(models.Model):
    image = models.ImageField(upload_to='retail-products-variations/',null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    disabled = models.BooleanField(default=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.created_date)

class RetailProductsVariations(models.Model):
    description = models.TextField(null=True,blank=True)
    variation = models.ManyToManyField(RetailVariation, related_name = "products", blank=True)
    product = models.ForeignKey(RetailProducts, on_delete=models.CASCADE, related_name = 'products_variations')

    price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00)

    specifications = models.JSONField(null=True, blank=True)
    
    stock_quantity = models.PositiveBigIntegerField(default = 0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    sku = models.CharField(max_length = 50)

    variations_image = models.ManyToManyField(ProductsVariationsImage, related_name = 'variations', blank=True)

    disabled = models.BooleanField(default=False)

    
    def __str__(self) -> str:
        return self.sku    

SKU_LENGTH = 7

def generate_sku(provided_name, vendor_id):
    try:
        count = RetailProductsVariations.objects.all().order_by("id").last().id + 1
        count = str(count)
    except:
        count = str(1)
    
    unique_id = "V" + str(vendor_id) + provided_name
    if RetailProductsVariations.objects.filter(sku = unique_id):
        similar_count = RetailProductsVariations.objects.filter(sku__icontains = unique_id).count()
        unique_id = "V" + str(vendor_id) + provided_name +str(similar_count)
 
    return unique_id

class ProductRequest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    product_name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)

class SearchKeyword(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name='search_keyword', null=True, blank=True)
    keyword = models.CharField(max_length=255)
    search_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.keyword