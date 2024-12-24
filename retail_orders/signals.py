from django.dispatch import receiver
from django.db.models.signals import post_save

from user.utils import mobile_message
from utils.mail import send_mail_using_graph
from django.template.loader import render_to_string
from urllib.parse import urljoin
from rest_framework.exceptions import ValidationError

from retail_orders.models import OrderedProduct, OrderedProductStatus
from user.models import Notification

from dvls import settings
domain = settings.DOMAIN

def set_notification(instance, title, message, link, notification_image):
    notification = Notification.objects.create(
            title = title,
            message = message,
            link = link,
            image = notification_image
        )

    notification.user.add(instance.ordered_product.order.user)

def send_email(instance, mail_subject, mail_template, link, image):
    context = {
        "to_email" : instance.ordered_product.order.user.email,
        "order" : instance.ordered_product.order,
        "product" : instance.ordered_product.product_variation.product,
        "product_variation" : instance.ordered_product.product_variation,
        "image" :  image if image else None,
        "link" : link,
        "user":  instance.ordered_product.order.user
    }

    send_mail_using_graph(
        receiver_email=context['to_email'], 
        subject=mail_subject, 
        message_text=render_to_string(mail_template, context)
    )

@receiver(post_save, sender=OrderedProductStatus)
def order_product_status(sender, instance, **kwargs):
    link = f"{settings.PROTOCOL}{settings.DOMAIN}/account/my-order/track/{instance.ordered_product.order.order_number}/{instance.ordered_product.product_variation.id}"
    
    notification_image = instance.ordered_product.product_variation.variations_image.first().image if instance.ordered_product.product_variation.variations_image.exists() else instance.ordered_product.product_variation.product.default_image

    variation_image = instance.ordered_product.product_variation.variations_image.first().image.url if instance.ordered_product.product_variation.variations_image.exists() else instance.ordered_product.product_variation.product.default_image.url
    image = urljoin(f"https://{domain}", variation_image) if variation_image else None

    order_num=str(instance.ordered_product.order.order_number)
    sliced_order_number = order_num.split("-")[4]

    match instance.status.status_code:
        case "001":
            title = "Order placed!"
            message = "Your order is placed successfully."
            set_notification(instance, title, message, link, notification_image)

        case "002":
            title = "Order accepted!"
            message = "Your order is accepted."
            set_notification(instance, title, message, link, notification_image)

            # send email
            mail_subject = "Order accepted!"
            mail_template = "notification/order_accepted.html"
            send_email(instance, mail_subject, mail_template, link, image)

            # send mobile sms
            nation = instance.ordered_product.order.nation
            phone_number = instance.ordered_product.order.phone
            message = f"Your Order- {sliced_order_number} has been accepted. Track your order here:{link} -Majjakodeals"
            
            response = mobile_message(phone_number, nation, message)
           
        
        case "003":
            title = "Rider reached vendor!"
            message = "Rider reached to vendor."
            set_notification(instance, title, message, link, notification_image)
        
        case "004":
            title = "Rider assigned!"
            message = "Yourreider has been assigned."
            set_notification(instance, title, message, link, notification_image)
        
        case "005":
            title = "Item reached our logistics!"
            message = "Item reached our logistics."
            set_notification(instance, title, message, link, notification_image)
        
        case "006":
            title = "Order dispatched!"
            message = "Your order has been dispatched. You will receive it soon."
            set_notification(instance, title, message, link, notification_image)

            # send email 
            mail_subject = "Order dispatched!"
            mail_template = "notification/order_dispatched.html"
            send_email(instance, mail_subject, mail_template, link, image)

            # send mobile sms
            nation = instance.ordered_product.order.nation
            phone_number = instance.ordered_product.order.phone
            message = f"Your Order- {sliced_order_number} has been dispatched. Track your order here:{link} -Majjakodeals"
           
            response = mobile_message(phone_number, nation, message)
            
        
        case "007":
            title = "QC passed!"
            message = "Quality checked."
            set_notification(instance, title, message, link, notification_image)
        
        case "008":
            title = "Order delivered!"
            message = "Your order has been delivered to you. Please leave your review."
            link =  f"{settings.PROTOCOL}{settings.DOMAIN}/account/delivered/{instance.ordered_product.order.order_number}"
            set_notification(instance, title, message, link, notification_image)

            # send email 
            mail_subject = "Order delivered!"
            mail_template = "notification/order_completed.html"
            send_email(instance, mail_subject, mail_template, link, image)

            # send mobile sms
            nation = instance.ordered_product.order.nation
            phone_number = instance.ordered_product.order.phone
            message = f"Your Order- {sliced_order_number} has been delivered. Track your order here:{link} -Majjakodeals"
            
            response = mobile_message(phone_number, nation, message)
            
        
        case "009":
            title = "Order cancelled!"
            message = "Your order has been cancelled."
            set_notification(instance, title, message, link, notification_image)
        
        case "010":
            title = "Item passed to other rider!"
            message = "Item passed to other rider."
            set_notification(instance, title, message, link, notification_image)
        
        case "011":
            title = "Item handed over to customer!"
            message = "Item handed over to customer."
            set_notification(instance, title, message, link, notification_image)

            # order completed when all ordered_product has status 011
            order = instance.ordered_product.order
            ordered_products = OrderedProduct.objects.filter(order=order)
            completed = True

            for product in ordered_products:
                statuses = product.status.all()
                if statuses:
                    for status in statuses:
                        if status.status.status_code != "011":
                            completed = False
                            break
                
                if not completed:
                    break

            if completed:
                order.status = "Completed"
                order.save()
        
        case "012":
            title = "Rider set off for delivery!"
            message = "Rider set off for delivery."
            set_notification(instance, title, message, link, notification_image)