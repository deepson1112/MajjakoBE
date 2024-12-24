import django_filters

from retail_review.models import Review

class ReviewFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name='ordered_product__product_variation__product', label='product')
    reply = django_filters.BooleanFilter(method="filter_reply_review")
    
    class Meta:
        model = Review
        fields = ['product']
    
    def filter_reply_review(self, queryset, name, value):
        if value == True:
            return queryset.filter(reply__isnull=False).exclude(reply="")
        elif value == False:
            return queryset.filter(reply__isnull=True) | queryset.filter(reply="")
        else:
            return queryset