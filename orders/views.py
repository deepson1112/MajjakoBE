import json
from django.conf import settings
from django.forms import model_to_dict
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
import stripe
from django.utils import timezone
from menu.models import Customization
from offers.models import LoyaltySettings
from orders.generate_pdf_labels import generate_pdf_labels 
from orders.models import Order, OrderCustomization, OrderedFood, OrdersTaxDetails, Payment, PaymentInfo, VendorInvoices, VendorsOrders
from orders.serializers import OrdersSerializer, OrdersTaxDetailsSerializer, PaymentsSerializers, VendorInvoicesSerializer
# Create your views here.
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.db.models import F, Subquery, OuterRef, JSONField, Prefetch
from django.db import models
from user.models import UserProfile
from utils.mail import send_mail_using_graph, send_notification
from utils.permissions_override import IsVendor
from django_filters.rest_framework import DjangoFilterBackend

class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentsSerializers

from rest_framework.permissions import IsAuthenticated
class OrdersViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_number']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # order_number = self.request.query_params.get("order_number","")
        # user = self.request.user
        # if order_number != "":
        #     try:
        #         return Order.objects.filter(order_number=order_number)
        #     except Order.DoesNotExist:
        #         raise ValidationError({"message":"Order Doesnot exist"})
        # else:
        #     if user.role == 1:
        #         return Order.objects.filter(user=user)
        return Order.objects.filter(user = self.request.user)

    
    def list(self, request, *args, **kwargs):
        query_set = self.queryset
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class VendorOrdersViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_number']
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Order.objects.filter(order_vendor__vendor__user = self.request.user)


class VendorInvoicesViewSet(ModelViewSet):
    queryset = VendorInvoices.objects.all()
    serializer_class = VendorInvoicesSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return VendorInvoices.objects.filter(vendor__user = self.request.user)


class OrderTaxDetailsViewSet(ModelViewSet):
    queryset = OrdersTaxDetails.objects.all()
    serializer_class= OrdersTaxDetailsSerializer


class ConfirmOrderView(ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentsSerializers

    def list(self, request, *args, **kwargs):
        order_number = self.request.query_params.get('order_number')
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            raise ValidationError({"message":"The order doesnot exist"})
        session_id = self.request.query_params.get('session_id')

        stripe.api_key = settings.STRIPE_API_KEY
        try:
            session =stripe.checkout.Session.retrieve(
            session_id, expand=['payment_intent.payment_method']
            )
        except Exception as e:
            raise ValidationError({"message":str(e)})
        
        if Payment.objects.filter(transaction_id = session_id).exists():
            raise ValidationError({"message":"The session of stripe is not accurate"})
        
        payment = Payment.objects.create(
            user = order.user,
            transaction_id = session.id,
            payment_method = 'Stripe',
            amount = session.amount_subtotal,
            status = session.status,
            created_at = timezone.now()
        )
        PaymentInfo.objects.create(
            payment = payment,
            session_id = session.id,
            payment_intent_id = session.payment_intent.id,
            card_last4 = session.payment_intent.payment_method.card.last4,
            card_brand=session.payment_intent.payment_method.card.brand,
            customer_name= session.customer_details.name,
            customer_email=session.customer_details.email,
            customer_phone=session.customer_details.phone,
        )

        order = Order.objects.get(order_number=order_number)
        if order.payment == None:
            order.payment = payment
            order.save()

            # send_mail background Task
            mail_subject = 'Thank you for ordering with us.'
            mail_template = 'orders/order_confirmation.html'
            ordered_food = OrderedFood.objects.filter(order=order).annotate(food_name = F('food_item__food_title')).values()
            customer_subtotal = 0
            customer_return = []
            for item in ordered_food:
                item['addons'] = list(OrderCustomization.objects.filter(food__id = item['id'])
                                               .annotate(customization_name = F('customization__title'))
                                               .annotate(addon_name = F('customization__title')).values())
                customer_return.append(item)
                customer_subtotal += (item['price'] * item['quantity'])

            
            customer_subtotal = round(customer_subtotal, 2)


            context = {
                'user': order.user,
                'order': order,
                'to_email': order.email,
                'ordered_food': customer_return,
                'domain': get_current_site(request),
                'customer_subtotal': customer_subtotal,
                'tax_data': {"test":"test"},
                'delivery_charge': order.delivery_charge,
                'coupon_discount': 1,
                'tip': order.tip,
            }
            send_notification(mail_subject, mail_template, context)
            

            #Send mail to the vendor
            each_vendor_orders = VendorsOrders.objects.filter(order__order_number = order_number)

            for each_vendors in each_vendor_orders:
                invoices = VendorInvoices.objects.create(
                    order = order,
                    vendor_name = each_vendors.vendor.vendor_name,
                    vendor = each_vendors.vendor,
                    subtotal = each_vendors.total_amount,
                    grand_total = each_vendors.total_amount,
                    total_discount = each_vendors.discounted_amount,
                    created_at = timezone.now(),
                    total_tax = each_vendors.total_tax
                )
                invoices.ordered_food.set(OrderedFood.objects.filter(order__order_number = order.order_number, food_item__vendor = each_vendors.vendor))


                mail_subject = 'You have received a new order.'
                mail_template = 'orders/new_order_received.html'

                user_orders = OrderedFood.objects.filter(
                    order__order_number=order.order_number, vendor_order = each_vendors).prefetch_related(
                                        Prefetch('order_food_addons', queryset=OrderCustomization.objects.select_related('customization')
                                                )).annotate(order_addons = F('order_food_addons'))
                
                vendor_sub_total = each_vendors.total_amount - each_vendors.total_tax
            
                new_items = []
                
                return_food_items = OrderedFood.objects.filter(
                    order__order_number=order_number, food_item__vendor=each_vendors.vendor).annotate(food_name = F('food_item__food_title')).values()
                
                for return_each_item in return_food_items:
                    return_each_item['addons'] = list(OrderCustomization.objects.filter(food__id = return_each_item['id'])
                                               .annotate(customization_name = F('customization__title'))
                                               .annotate(addon_name = F('customization__title')).values())
                    new_items.append(return_each_item)
                context = {
                        'order': order,
                        'to_email': each_vendors.vendor.user.email,
                        'ordered_food_to_vendor': new_items,
                        'vendor_subtotal': vendor_sub_total,
                        'tax_data':each_vendors.total_tax,
                        'vendor_grand_total': each_vendors.total_amount,

                    }

                    # Send email to this vendor
            
                filtered_data = []


                for each_item in user_orders:
                    addon = []
                    # [ order_addon.addons.title if order_addon.addons else "No Addon"  for order_addon in each_item.order_addons]
                    addons = OrderCustomization.objects.filter(food=each_item)
                    if addons.exists():
                        addons_data = addons.values_list('customization__title', flat=True)
                        receiver_name = each_item.receiver_name
                    else :
                        addons_data = ["NO Addons"]
                        receiver_name = each_item.receiver_name


                    filtered_data.append(
                        (each_item.food_item.food_title,addons_data, receiver_name,each_vendors.vendor.vendor_name)
                    )
                
                filename = generate_pdf_labels(
                        order.order_number, each_vendors.vendor.vendor_name,food_items=filtered_data)

                send_mail_using_graph(attachments=filename,
                                        receiver_email=context['to_email'], subject=mail_subject, message_text=render_to_string(mail_template, context))

            user = order.user
            user_profile = UserProfile.objects.get(user=user)

            if LoyaltySettings.objects.all().exists():
                loyalty = LoyaltySettings.objects.first()
                total_transaction = payment.amount
                amount_received = total_transaction / loyalty.in_amount
                user_profile.loyalty_points = user_profile.loyalty_points +  amount_received
                order.loyalty_points_received = total_transaction / loyalty.in_amount
                order.save()
                user_profile.save()

            return redirect("https://chowchow-express-next-js.vercel.app/order-confirmation?order_number="+order_number)
        else:
            raise ValidationError({"message":"The payment for the order is already completed"})

