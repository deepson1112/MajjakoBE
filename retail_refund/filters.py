import django_filters

from retail_refund.models import RetailRefund

class RetailRefundFilter(django_filters.FilterSet):
    vendor = django_filters.NumberFilter(field_name='refund_products__product_variation__product__vendor')

    class Meta:
        model = RetailRefund
        fields = ['vendor']