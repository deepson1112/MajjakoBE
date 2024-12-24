from django.apps import AppConfig


class RetailOrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'retail_orders'

    def ready(self):
        import retail_orders.signals