from django.db.models.signals import post_save, post_delete,  m2m_changed
from django.dispatch import receiver
from django.urls import reverse
from django.core.cache import cache

from retail_offers.models import RetailGetOneFreeOffer, RetailSaveOnItemsDiscountPercentage, RetailStoreOffer
from .models import RetailProducts, RetailProductsVariations


def delete_product_cache(product_ids):
    for product_id in product_ids:
        cache_key = f"retail_product_{product_id}"
        cache.delete(cache_key)

@receiver(post_save, sender=RetailProducts)
@receiver(post_delete, sender=RetailProducts)
def invalidate_product_cache(sender, instance, **kwargs):
    delete_product_cache([instance.id])

@receiver(post_save, sender=RetailProductsVariations)
@receiver(post_delete, sender=RetailProductsVariations)
def invalidate_variation_cache(sender, instance, **kwargs):
    if instance.product:
        delete_product_cache([instance.product.id])

@receiver(post_save, sender=RetailStoreOffer)
@receiver(post_delete, sender=RetailStoreOffer)
def invalidate_storeoffer_cache(sender, instance, **kwargs):
    products = RetailProducts.objects.filter(vendor=instance.vendor.id).values_list('id', flat=True)
    delete_product_cache(products)

@receiver(post_save, sender=RetailSaveOnItemsDiscountPercentage)
@receiver(post_delete, sender=RetailSaveOnItemsDiscountPercentage)
def invalidate_saveonitem_cache(sender, instance, **kwargs):
    product_ids = set()

    if instance.retail_product:
        product_ids.add(instance.retail_product.id)
    
    if instance.retail_product_variation:
        product_ids.add(instance.retail_product_variation.product.id)

    if instance.sub_category:
        sub_category_products = RetailProducts.objects.filter(sub_category=instance.sub_category).values_list('id', flat=True)
        product_ids.update(sub_category_products)
    
    if instance.offer_category:
        offer_category_products = instance.offer_category.products.values_list('id', flat=True)
        product_ids.update(offer_category_products)

    delete_product_cache(product_ids)

@receiver(m2m_changed, sender=RetailGetOneFreeOffer.retail_products.through)
@receiver(post_delete, sender=RetailGetOneFreeOffer)
def invalidate_getonefree_cache(sender, instance, **kwargs):
    products = instance.retail_products.values_list('id', flat=True)
    delete_product_cache(products)