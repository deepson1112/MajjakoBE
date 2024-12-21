from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import path
from django import forms
from retail.models import RetailProducts, RetailProductsVariations, RetailVariation, RetailVariationType, ProductsVariationsImage, RefundPolicy, ProductRequest, SearchKeyword
from menu.models import VendorCategories, VendorDepartment


# Register your models here.

class CategoryChangeForm(forms.Form):
    """Form for selecting a new category."""
    new_category = forms.ModelChoiceField(
        queryset=VendorDepartment.objects.all(),
        required=True,
        label="Select New Category"
    )
class SubCategoryChangeForm(forms.Form):
    """Form for selecting a new category."""
    new_sub_category = forms.ModelChoiceField(
        queryset=VendorCategories.objects.all(),
        required=True,
        label="Select New Sub-Category"
    )


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_complete']
    actions = ['completed', 'incomplete', 'enabled', 'disabled', 'bulk_change_category', 'bulk_change_sub_category', 'enable_special_request', 'disable_special_request']
    search_fields = ['name']
    list_filter = ['vendor', 'category', 'sub_category', 'is_complete']

    @admin.action(description='Completed')
    def completed(self, request, queryset):
        queryset.update(is_complete=True)

    @admin.action(description='Incomplete')
    def incomplete(self, request, queryset):
        queryset.update(is_complete=False)

    @admin.action(description='Disabled')
    def disabled(self, request, queryset):
        queryset.update(disabled=True)

    @admin.action(description='Enabled')
    def enabled(self, request, queryset):
        queryset.update(disabled=False)

    @admin.action(description='Enable Special Request')
    def enable_special_request(self, request, queryset):
        queryset.update(special_request=True)

    @admin.action(description='Disable Special Request')
    def disable_special_request(self, request, queryset):
        queryset.update(special_request=False)



    @admin.action(description='Bulk Change Category')
    def bulk_change_category(self, request, queryset):
        """
        Redirect to a custom form for selecting the category.
        """
        selected = request.POST.getlist("_selected_action")
        if not selected:
            self.message_user(request, "No items selected.", level=messages.WARNING)
            return

        return redirect(f"bulk-change-category/?ids={','.join(selected)}")

    @admin.action(description='Bulk Change Sub-Category')
    def bulk_change_sub_category(self, request, queryset):
        """
        Redirect to a custom form for selecting the sub-category.
        """
        selected = request.POST.getlist("_selected_action")
        if not selected:
            self.message_user(request, "No items selected.", level=messages.WARNING)
            return

        return redirect(f"bulk-change-sub-category/?ids={','.join(selected)}")

    def get_urls(self):
        """Add a custom URL for the bulk change category form."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'bulk-change-category/',
                self.admin_site.admin_view(self.bulk_change_category_view),
                name='bulk_change_category_form'
            ),
            path(
                'bulk-change-sub-category/',
                self.admin_site.admin_view(self.bulk_change_sub_category_view),
                name='bulk_change_sub_category_form'
            )
        ]
        return custom_urls + urls

    def bulk_change_category_view(self, request):
        """Custom view for the bulk change category form."""
        ids = request.GET.get('ids', '').split(',')
        if not ids:
            self.message_user(request, "No items selected.", level=messages.WARNING)
            return redirect('..')

        products = RetailProducts.objects.filter(id__in=ids)
        if request.method == 'POST':
            form = CategoryChangeForm(request.POST)
            if form.is_valid():
                new_category = form.cleaned_data['new_category']
                updated_count = products.update(category=new_category)
                self.message_user(
                    request,
                    f"Successfully updated category for {updated_count} products to {new_category.department_name}.",
                    level=messages.SUCCESS
                )
                return redirect('..')
        else:
            form = CategoryChangeForm()

        context = {
            'form': form,
            'products': products,
            'title': 'Bulk Change Category',
        }
        return render(request, 'admin/bulk_change_category.html', context)

    def bulk_change_sub_category_view(self, request):
        """Custom view for the bulk change sub-category form."""
        ids = request.GET.get('ids', '').split(',')
        if not ids:
            self.message_user(request, "No items selected.", level=messages.WARNING)
            return redirect('..')

        products = RetailProducts.objects.filter(id__in=ids)
        if request.method == 'POST':
            form = SubCategoryChangeForm(request.POST)
            if form.is_valid():
                new_sub_category = form.cleaned_data['new_sub_category']
                updated_count = products.update(sub_category=new_sub_category)
                self.message_user(
                    request,
                    f"Successfully updated sub-category for {updated_count} products to {new_sub_category.category_name}.",
                    level=messages.SUCCESS
                )
                return redirect('..')
        else:
            form = SubCategoryChangeForm()

        context = {
            'form': form,
            'products': products,
            'title': 'Bulk Change Sub-Category',
        }
        return render(request, 'admin/bulk_change_sub_category.html', context)


class RetailProductsVariationsAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'stock_quantity']
    search_fields = ['sku', 'product__name']

admin.site.register(RetailVariationType)
admin.site.register(RetailVariation)
admin.site.register(RetailProducts, ProductAdmin)
admin.site.register(RetailProductsVariations, RetailProductsVariationsAdmin)
admin.site.register(ProductsVariationsImage)
admin.site.register(RefundPolicy)
admin.site.register(ProductRequest)
admin.site.register(SearchKeyword)
