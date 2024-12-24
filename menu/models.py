import uuid
from django.db import models
from django.utils.text import slugify
from vendor.models import Vendor, VendorHourTimelines

VENDOR_TYPE = (
        (1, "Restaurant"),
        (2, "Retails")
    )

class VendorDepartment(models.Model):
    department_name = models.CharField(
        max_length=255, help_text="Department name")
    department_slug = models.SlugField()
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)
    tax_rate = models.FloatField(default=0.0)
    tax_exempt = models.BooleanField(default=False)
    age_restriction = models.BooleanField(default=False)

    hours_schedule = models.ForeignKey(
        VendorHourTimelines, null=True, blank=True, on_delete=models.CASCADE)
    
    image = models.ImageField('department/', null=True, blank=True)

    vendor_type = models.PositiveSmallIntegerField(
        choices = VENDOR_TYPE, default = 2, null=True
    )
    
    department_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['department_order']

    def __str__(self) -> str:
        return self.department_name
    

    def save(self, **kwargs):
        if not self.department_slug:
            self.department_slug = slugify(self.department_name)
            unique_id = uuid.uuid4().hex[:6]
            self.department_slug = self.department_slug + unique_id

        return super(VendorDepartment, self).save(**kwargs)


class VendorCategories(models.Model):
    department = models.ForeignKey(VendorDepartment, on_delete=models.CASCADE, null=True, related_name='vendor_categories')
    category_name = models.CharField(max_length=255)
    category_slug = models.SlugField()
    category_description = models.TextField(null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)
    tax_rate = models.FloatField(default=0.0)
    tax_exempt = models.BooleanField(default=False)
    age_restriction = models.BooleanField(default=False)
    hours_schedule = models.ForeignKey(
        VendorHourTimelines, null=True, on_delete=models.CASCADE, blank=True)
    active = models.BooleanField(default=True)

    categories_order = models.IntegerField(default=0)

    image = models.ImageField('department/', null=True, blank=True)

    vendor_type = models.PositiveSmallIntegerField(
        choices = VENDOR_TYPE, default = 2, null=True
    )

    def __str__(self) -> str:
        return self.category_name

    def save(self, **kwargs):
        if not self.category_slug:
            self.category_slug = slugify(self.category_name)
            unique_id = uuid.uuid4().hex[:6]
            self.category_slug = self.category_slug + unique_id

        return super(VendorCategories, self).save(**kwargs)
    
    class Meta:
        ordering = ['categories_order']


# class Category(models.Model):
#     category_name = models.CharField(max_length=50)
#     slug = models.SlugField(max_length=100, unique=True)
#     description = models.TextField(max_length=250, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = 'category'
#         verbose_name_plural = 'categories'

#     def save(self, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.category_name)
#             unique_id = uuid.uuid4().hex[:6]
#             self.slug = self.slug + unique_id

#         return super(Category, self).save(**kwargs)

#     def clean(self):
#         self.category_name = self.category_name.capitalize()

#     def __str__(self):
#         return self.category_name


class FoodItem(models.Model):
    vendor_categories = models.ForeignKey(
        VendorCategories, on_delete=models.CASCADE, null=True)
    food_title = models.CharField(max_length=50)
    description = models.TextField(max_length=250, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='foodimages', null=True)
    is_available = models.BooleanField(default=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    hours_schedule = models.ForeignKey(
        VendorHourTimelines, null=True, on_delete=models.CASCADE)
    
    food_item_order = models.IntegerField(default=1)

    def __str__(self):
        return self.food_title

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.food_title)
            unique_id = uuid.uuid4().hex[:6]
            self.slug = self.slug + unique_id

        return super(FoodItem, self).save(**kwargs)


class CustomizationTitle(models.Model):
    SELECT_TYPE = (
        ("SINGLE", "SINGLE"),
        ("MULTIPLE", "MULTIPLE")
    )
    minimum_quantity = models.PositiveSmallIntegerField() #maxi
    maximum_quantity = models.FloatField()
    
    description = models.TextField(null=True)

    add_on_category = models.CharField(max_length=255)
    select_type = models.CharField(
        max_length=225, choices=SELECT_TYPE, default="SINGLE")
    created_by = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    
    def __str__(self) -> str:
        return self.add_on_category



class Customization(models.Model):
    customization_title = models.ForeignKey(
        CustomizationTitle, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.FloatField()
    maximum_number = models.IntegerField(default=0)
    description = models.CharField(
        max_length=225,
        null=True,
        help_text="This is the description for the addons, max_length = 255")
    image = models.ImageField(upload_to="addons/", blank=True, null=True)

    created_by = models.ForeignKey(Vendor, on_delete = models.CASCADE, null=True)
    multiple_selection = models.BooleanField(default=False)
    secondary_customization = models.BooleanField(default=False)
    customization = models.ForeignKey(CustomizationTitle, null=True,on_delete= models.CASCADE, related_name = "sec_customization")
    customization_order = models.IntegerField(default=1)


    def __str__(self) -> str:
        return self.title


class FoodAddonsFoodJunction(models.Model):
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    
    categories = models.ForeignKey(
        CustomizationTitle,
        on_delete=models.CASCADE, related_name="food_addons")
    
    food_addons_order = models.IntegerField(default=1)

    # class Meta:
    #     unique_together = ('food_item', 'categories')



