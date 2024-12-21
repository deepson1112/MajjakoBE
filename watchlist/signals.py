from decimal import Decimal
from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from user.models import Notification
from utils.mail import send_mail_using_graph
from django.template.loader import render_to_string
from urllib.parse import urljoin
from django.utils import timezone

from retail.models import RetailProducts, RetailProductsVariations
from retail_offers.models import RetailGetOneFreeOffer, RetailSaveOnItemsDiscountPercentage, RetailSaveOnItemsOffer, RetailStoreOffer
from watchlist.models import WatchList

from dvls.settings import DOMAIN

import environ
env = environ.Env()

domain = env.str('DOMAIN')

@receiver(pre_save, sender=RetailProductsVariations)
def store_old_product_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = RetailProductsVariations.objects.get(pk=instance.pk)
        except RetailProductsVariations.DoesNotExist:
            instance._old_instance = None

@receiver(post_save, sender=RetailProductsVariations) 
def notify_users_on_product_change(sender, instance, **kwargs):
    # Check if there's an old instance to compare with
    if hasattr(instance, '_old_instance') and instance._old_instance:

        old_instance = instance._old_instance
        watchlists = WatchList.objects.filter(product_variation=instance.id)
        users = [watchlist.user for watchlist in watchlists]

        watchlist = WatchList.objects.filter(product_variation=instance).first()
        if watchlist:

            variation_image = watchlist.product_variation.variations_image.first().image.url if watchlist.product_variation.variations_image.all() else None
            image_url = urljoin(f"https://{domain}", variation_image) if variation_image else None

            # Check if the stock quantity is running low
            if old_instance.stock_quantity != instance.stock_quantity and instance.stock_quantity != 0 and instance.stock_quantity < 5:
                notification = Notification.objects.create(
                    title = "Stock is running out",
                    message = f"{ watchlist.product_variation.product.name} is running out of stock. Grab yours before it gets sold out.",
                    link = f"https://{DOMAIN}/bazar/products/{watchlist.product_variation.product.sub_category.id}/{watchlist.product_variation.product.id}",
                    image =  image_url if image_url else None,
                )
                notification.user.set(users)
            
            for user in users: 
                mail_subject = "Stock is running out"
                mail_template = "watchlist/stock_reduced.html"

                context = {
                    "to_email" : user.email,
                    "product" : watchlist.product_variation.product,
                    "product_variation" : watchlist.product_variation,
                    "variation_image" :  image_url if image_url else None,
                    "itme_link" : f"https://{DOMAIN}/bazar/products/{watchlist.product_variation.product.sub_category.id}/{watchlist.product_variation.product.id}"
                }

                send_mail_using_graph(
                    receiver_email=context['to_email'], 
                    subject=mail_subject, 
                    message_text=render_to_string(mail_template, context)
                )

            #Out of stock
            if old_instance.stock_quantity > 0 and instance.stock_quantity == 0:
                notification = Notification.objects.create(
                    title = "Product is out of stock.",
                    message = f"{ watchlist.product_variation.product.name} is out of stock. You will be notified when it gets restocked.",
                    link = f"https://{DOMAIN}/bazar/products/{watchlist.product_variation.product.sub_category.id}/{watchlist.product_variation.product.id}",
                    image =  image_url if image_url else None,
                )
                notification.user.set(users)

            for user in users: 
                mail_subject = "Out of stock"
                mail_template = "watchlist/out_of_stock.html"

                context = {
                    "to_email" : user.email,
                    "product" : watchlist.product_variation.product,
                    "product_variation" : watchlist.product_variation,
                    "variation_image" :  image_url if image_url else None,
                    "itme_link" : f"https://{DOMAIN}/bazar/products/{watchlist.product_variation.product.sub_category.id}/{watchlist.product_variation.product.id}"
                }
                send_mail_using_graph(
                    receiver_email=context['to_email'], 
                    subject=mail_subject, 
                    message_text=render_to_string(mail_template, context)
                )

            # Check if the product was out of stock and has been restocked
            if old_instance.stock_quantity != instance.stock_quantity and  old_instance.stock_quantity == 0 and instance.stock_quantity > 0:
                notification = Notification.objects.create(
                    title = "Product restocked ",
                    message = f"{ watchlist.product_variation.product.name} is restocked. Grab yours before it gets sold out.",
                    link = f"https://{DOMAIN}/bazar/products/{watchlist.product_variation.product.sub_category.id}/{watchlist.product_variation.product.id}",
                    image =  image_url if image_url else None,
                )
                notification.user.set(users)

            for user in users: 
                mail_subject = "Product is restocked"
                mail_template = "watchlist/restocked.html"

                context = {
                    "to_email" : user.email,
                    "product" : watchlist.product_variation.product,
                    "product_variation" : watchlist.product_variation,
                    "variation_image" :  image_url if image_url else None,
                    "itme_link" : f"https://{DOMAIN}/bazar/products/{watchlist.product_variation.product.sub_category.id}/{watchlist.product_variation.product.id}"
                }

                send_mail_using_graph(
                    receiver_email=context['to_email'], 
                    subject=mail_subject, 
                    message_text=render_to_string(mail_template, context)
                )
        				

# @receiver(pre_save, sender=RetailGetOneFreeOffer)
# def store_bogo(sender, instance, **kwargs):
#     if instance.pk:
#         try:
#             instance._old_instance = RetailGetOneFreeOffer.objects.get(pk=instance.pk)
#         except RetailGetOneFreeOffer.DoesNotExist:
#             instance._old_instance = RetailGetOneFreeOffer.objects.create()


@receiver(post_save, sender=RetailStoreOffer) 
def notify_users_on_store_offer_create(sender, instance, **kwargs):
    current_date = timezone.now()
    if instance.start_date <= current_date <= instance.end_date and instance.active==True:
        products = RetailProducts.objects.filter(vendor=instance.vendor)

        variations = []
        image_url=None

        for product in products:
            variations.extend(product.products_variations.values_list('id', flat=True))

        watchlists = WatchList.objects.filter(product_variation__in=variations)
        users = set(watchlist.user for watchlist in watchlists)

        product_variations = set(watchlist.product_variation for watchlist in watchlists)

        for variation in product_variations:
            if variation.variations_image.all():
                variation_image = variation.variations_image.first().image.url
                image_url = urljoin(f"https://{domain}", variation_image) if variation_image else None

            notification = Notification.objects.create(
                title="Offer!",
                message=f"Get exciting discount offer on {variation.product.name} product valid till {instance.end_date.date()}. Grab the opportunity.",
                link=f"https://{DOMAIN}/bazar/products/{variation.product.sub_category.id}/{variation.product.id}",
                image=image_url if image_url else None,
            )

            notification.user.set(users)

        for user in users:
            watchlists = WatchList.objects.filter(product_variation__in=variations, user=user)
            product_variation_details = []
            image_url = None
            
            for watchlist in watchlists:
                variation = watchlist.product_variation
                if variation.variations_image.all():
                    variation_image = variation.variations_image.first().image.url
                    image_url = urljoin(f"https://{domain}", variation_image) 
                
                old_price = variation.price
                discount = Decimal(instance.discount_percentages) / 100
                new_price = old_price - (old_price * discount)

                product_variation_details.append({
                    "product": variation.product,
                    "product_variation": variation,
                    "old_price": old_price,
                    "new_price": new_price,
                    "variation_image": image_url if image_url else None,
                    "itme_link" : f"https://{DOMAIN}/bazar/products/{variation.product.sub_category.id}/{variation.product.id}"
                })

            mail_subject = "Offer !!"
            mail_template = "watchlist/store_offer.html"

            context = {
                "to_email" : user.email,
                "product_variation_details": product_variation_details,
                "offer" : instance,

            }

            send_mail_using_graph(
                receiver_email=context['to_email'], 
                subject=mail_subject, 
                message_text=render_to_string(mail_template, context)
            )

@receiver(post_save, sender=RetailSaveOnItemsDiscountPercentage)
def notify_users_on_item_offer(sender, instance, **kwargs):
    current_date = timezone.now()
    if instance.store_offer.start_date <= current_date <= instance.store_offer.end_date and instance.store_offer.active==True:
        watchlists = None
        image_url = None

        if instance.retail_product_variation:
            watchlists = WatchList.objects.filter(product_variation=instance.retail_product_variation)
        
        if instance.retail_product:
            variations = RetailProductsVariations.objects.filter(product=instance.retail_product).values_list('id', flat=True)
            watchlists = WatchList.objects.filter(product_variation__in=variations)

        if instance.sub_category:
            variations = RetailProductsVariations.objects.filter(product__sub_category=instance.sub_category).values_list('id', flat=True)
            watchlists = WatchList.objects.filter(product_variation__in=variations)

        if watchlists:
            users = set(watchlist.user for watchlist in watchlists)
        
            product_variations = set(watchlist.product_variation for watchlist in watchlists)

            for variation in product_variations:
                if variation.variations_image.all():
                    variation_image = variation.variations_image.first().image.url
                    image_url = urljoin(f"https://{domain}", variation_image)

                notification = Notification.objects.create(
                    title="Offer!",
                    message=f"Get exciting discount offer on {variation.product.name} product valid till {instance.store_offer.end_date.date()}. Grab the opportunity.",
                    link=f"https://{DOMAIN}/bazar/products/{variation.product.sub_category.id}/{variation.product.id}",
                    image=image_url if image_url else None,
                )

                notification.user.set(users)
            
            for user in users:
                watchlists = watchlists.filter(user=user)
                product_variation_details = []
                
                for watchlist in watchlists:
                    variation = watchlist.product_variation
                    if variation.variations_image.all():
                        variation_image = variation.variations_image.first().image.url
                        image_url = urljoin(f"https://{domain}", variation_image)
                    
                    old_price = variation.price
                    discount = Decimal(instance.discount_percentages) / 100
                    new_price = old_price - (old_price * discount)

                    product_variation_details.append({
                        "product": variation.product,
                        "product_variation": variation,
                        "old_price": old_price,
                        "new_price": new_price,
                        "variation_image": image_url,
                        "itme_link" : f"https://{DOMAIN}/bazar/products/{variation.product.sub_category.id}/{variation.product.id}"
                    })

                mail_subject = "Offer !!"
                mail_template = "watchlist/store_offer.html"

                context = {
                    "to_email" : user.email,
                    "product_variation_details": product_variation_details,
                    "offer" : instance
                }

                send_mail_using_graph(
                    receiver_email=context['to_email'], 
                    subject=mail_subject, 
                    message_text=render_to_string(mail_template, context)
                )

@receiver(m2m_changed, sender=RetailGetOneFreeOffer.retail_products.through) 
def notify_users_on_store_offer_create(sender, instance, action, **kwargs):
    if action == "post_add":
        current_date = timezone.now()
        if instance.start_date <= current_date <= instance.end_date and instance.active==True:
            products = instance.retail_products.all()
            variations = []
            image_url = None

            for product in products:
                variations.extend(product.products_variations.values_list('id', flat=True))

            watchlists = WatchList.objects.filter(product_variation__in=variations)
            users = set(watchlist.user for watchlist in watchlists)

            product_variations = set(watchlist.product_variation for watchlist in watchlists)

            for variation in product_variations:
                if variation.variations_image.all():
                    variation_image = variation.variations_image.first().image.url
                    image_url = urljoin(f"https://{domain}", variation_image)

                notification = Notification.objects.create(
                    title="Offer!",
                    message=f"Buy One Get One offer on {variation.product.name} product valid till {instance.end_date.date()}. Grab the opportunity.",
                    link=f"https://{DOMAIN}/bazar/products/{variation.product.sub_category.id}/{variation.product.id}",
                    image=image_url if image_url else None,
                )

                notification.user.set(users)

            for user in users:
                watchlists = WatchList.objects.filter(product_variation__in=variations, user=user)
                product_variation_details = []

                for watchlist in watchlists:
                    variation = watchlist.product_variation
                    if variation.variations_image.all():
                        variation_image = variation.variations_image.first().image.url
                        image_url = urljoin(f"https://{domain}", variation_image)
                    
                    product_variation_details.append({
                        "product": variation.product,
                        "product_variation": variation,
                        "variation_image": image_url,
                        "itme_link" :f"https://chowchow.mydvls.com/bazar/products/{variation.product.sub_category.id}/{variation.product.id}"
                    })

                mail_subject = "Buy One Get One Offer"
                mail_template = "watchlist/bogo.html"

                context = {
                    "to_email" : user.email,
                    "product_variation_details": product_variation_details,
                    "offer" : instance
                }

                send_mail_using_graph(
                    receiver_email=context['to_email'], 
                    subject=mail_subject, 
                    message_text=render_to_string(mail_template, context)
                )