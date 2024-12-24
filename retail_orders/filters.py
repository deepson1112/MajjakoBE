import django_filters
from .models import OrderedProduct, RetailOrder
from django.utils import timezone
from django.db.models import Max
from django.db.models import F

class OrderedProductFilter(django_filters.FilterSet):
    vendor = django_filters.NumberFilter(field_name='vendor_order__vendor')
    date = django_filters.DateFilter(field_name='created_at', lookup_expr='date')
    product = django_filters.CharFilter(field_name='product_variation__product__name', lookup_expr='exact')

    week = django_filters.NumberFilter(method='filter_weekly', label="Weekly")
    month = django_filters.NumberFilter(method='filter_monthly', label="Monthly")
    year = django_filters.NumberFilter(method='filter_year', label="Year")

    status = django_filters.CharFilter(method='filter_status', label='Status')

    payment_method = django_filters.CharFilter(field_name='order__payment_method')

    payment_status = django_filters.CharFilter(field_name='order__payment__status')

    seen = django_filters.BooleanFilter(field_name='seen')

    class Meta:
        model = OrderedProduct
        fields = ['vendor', 'date', 'product', 'week', 'month', 'year', 'status', 'payment_method', 'payment_status']
    
    def filter_year(self, queryset, name, value): 
        if value:
            return queryset.filter(created_at__year=value)
        return queryset
    
    def filter_monthly(self, queryset, name, month):
        if month and 1 <= month <= 12:
            year = self.data.get('year')
            if year:
                return queryset.filter(created_at__year=year, created_at__month=month)
            return queryset.filter(created_at__month=month)
        return queryset
    
    def filter_weekly(self, queryset, name, value):
        if value:
            year = self.data.get('year')
            month = self.data.get('month')

            if year and month and value:

                first_day_of_month = timezone.datetime(year=int(year), month=int(month), day=1).date()

                start_of_week = first_day_of_month + timezone.timedelta(weeks=int(value) - 1)
                start_of_week = start_of_week - timezone.timedelta(days=start_of_week.weekday())  # Adjust to the start of the week (Monday)
                
                end_of_week = start_of_week + timezone.timedelta(days=7)
                
                return queryset.filter(
                    created_at__date__gte=start_of_week,
                    created_at__date__lt=end_of_week,
                    created_at__year=year,
                    created_at__month=month
                )
        return queryset
    

    def filter_status(self, queryset, name, status):
        queryset = queryset.annotate(latest_status_date=Max('status__created_at'))
    
        if status == "completed":
            return queryset.filter(status__closed=True, status__created_at=F('latest_status_date')).distinct()
        elif status == "pending":
            return queryset.filter(status__closed=False, status__created_at=F('latest_status_date')).distinct()
        else:
            return queryset.all()
        