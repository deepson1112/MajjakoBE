from django.contrib import admin

from menu.models import  Customization, CustomizationTitle, FoodItem, VendorDepartment, FoodAddonsFoodJunction

from menu.models import  Customization, FoodItem, VendorDepartment, FoodAddonsFoodJunction, VendorCategories

class VendorDepartmentAdmin(admin.ModelAdmin):
    list_display = ['department_name']
    search_fields = ['department_name']


class VendorCategoriesAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'department']
    search_fields = ['category_name']
    list_filter = ['department']


# admin.site.register(FoodItem)
admin.site.register(VendorDepartment, VendorDepartmentAdmin)
# admin.site.register(FoodAddonsFoodJunction)
# admin.site.register(Customization)
# admin.site.register(CustomizationTitle)
admin.site.register(VendorCategories, VendorCategoriesAdmin)
