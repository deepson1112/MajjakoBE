from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError, NotAcceptable
from collections import defaultdict
from django.utils import timezone
import uuid
from datetime import time, date, datetime
from django.db.models import Q

from retail.models import RetailProducts, RetailProductsVariations

from retail_marketplace.utils import generate_esewa_signature
from retail_offers.models import RetailCoupon, RetailFreeDelivery, RetailLoyaltyPrograms
from retail_offers.serializers import RetailCouponSerializer
from retail_orders.models import OrderStatus, OrderedProduct, OrderedProductStatus, RetailOrder, RetailVendorOrder
from retail_orders.views import ConfirmRetailOrderView
from retail_wishlist.models import SharedRetailWishlist
from retail_wishlist.serializers import SharedRetailWishlistSerializer
from user.models import UserLocation
from utils.check_delivery_zone import check_delivery_zone
from vendor.models import Vendor
from vendor.serializers import VendorSerializer

from .models import RetailCart, RetailDeliveryCharge
from .serializers import  RetailCartCalculationSerializer, RetailCartSerializer, RetailDeliveryChargeSerializer, UserRetailCartSerializer

from rest_framework.permissions import IsAuthenticated

import stripe
from dvls import settings
import requests
# from settings import ESEWA_CONDIG

from django.shortcuts import redirect

stripe.api_key = settings.STRIPE_API_KEY

from dvls.settings import DEBUG

if DEBUG:
    base_url = "dev.majjakodeals.com"
else:
    base_url = "test.majjakodeals.com"


import math
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Radius of Earth in kilometers. Use 3956 for miles.
    r = 6371.0
    
    # Calculate the result
    distance = r * c
    
    return distance

# Create your views here.

class RetailCartViewSet(ModelViewSet):
    queryset = RetailCart.objects.filter(active=True).filter(shared_wishlist=True)
    serializer_class = RetailCartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RetailCart.objects.filter(user=self.request.user).filter(active=True, buy_now=False)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

class ClearRetailCartViewSet(ModelViewSet):
    queryset = RetailCart.objects.filter(active=True)
    serializer_class = RetailCartSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        query = RetailCart.objects.filter(user=self.request.user).filter(active=True)
        query.update(active=False)
        return Response({"message":"Cart emptied"}, status=status.HTTP_200_OK)

class UserRetailCartViewSet(ModelViewSet):
    queryset = RetailCart.objects.filter(active=True)
    serializer_class = UserRetailCartSerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['retail_product_variation']

    def get_queryset(self):
        return RetailCart.objects.filter(user=self.request.user).filter(active=True)

class RetailCartItemCalculationViewSet(ModelViewSet):
    queryset = RetailCart.objects.filter(active=True)
    serializer_class = RetailCartCalculationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['retail_product_variation']

    def get_queryset(self):
        return RetailCart.objects.filter(user=self.request.user).filter(active=True)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        current_time = timezone.now()
        
        user_lat = None
        user_long = None

        loyalty_code =request.GET.get("loyalty_code", "")
        loyalty=None
        if loyalty_code:
            try:
                loyalty = RetailLoyaltyPrograms.objects.filter(disabled=False).get(program_code = loyalty_code)
            except RetailLoyaltyPrograms.DoesNotExist:
                raise ValidationError({"message":"The loyalty program does not exist"})

        shared_wishlist = request.GET.get("shared_wishlist", "")
        buy_now = request.GET.get("buy_now", "")

        vendor_data = []
        if shared_wishlist:
            try:
                shared = SharedRetailWishlist.objects.get(uuid=shared_wishlist)
                user_lat = shared.latitude
                user_long = shared.longitude
            except SharedRetailWishlist.DoesNotExist:
                raise ValidationError({"message": f"Shared wishlist uuid doesnot exists: {shared_wishlist}"})
            
            ordered_carts = RetailCart.objects.filter(user=request.user).filter(active=True, buy_now=False).exclude(shared_wishlist__isnull=True)
            vendors = RetailCart.objects.filter(user=request.user).filter(active=True, buy_now=False).exclude(shared_wishlist__isnull=True).distinct('retail_product_variation__product__vendor').values_list('retail_product_variation__product__vendor', flat=True)
        elif buy_now:
            ordered_carts = RetailCart.objects.filter(user=request.user).filter(active=True, buy_now=True)
            vendors = RetailCart.objects.filter(user=request.user).filter(active=True, buy_now=True).exclude(shared_wishlist__isnull=False).distinct('retail_product_variation__product__vendor').values_list('retail_product_variation__product__vendor', flat=True)
        else:
            ordered_carts = RetailCart.objects.filter(user=request.user).filter(active=True, buy_now=False).exclude(shared_wishlist__isnull=False)
            vendors = RetailCart.objects.filter(user=request.user).filter(active=True, buy_now=False).exclude(shared_wishlist__isnull=False).distinct('retail_product_variation__product__vendor').values_list('retail_product_variation__product__vendor', flat=True)

        for vendor in vendors:
            if shared_wishlist:
                cart_items = queryset.filter(retail_product_variation__product__vendor__id = vendor).exclude(shared_wishlist__isnull=True).filter(shared_wishlist=shared, buy_now=False)
            elif buy_now:
                cart_items = queryset.filter(retail_product_variation__product__vendor__id = vendor, buy_now=True).exclude(shared_wishlist__isnull=False)
            else:
                cart_items = queryset.filter(retail_product_variation__product__vendor__id = vendor, buy_now=False).exclude(shared_wishlist__isnull=False)
            serializer_data = self.get_serializer(cart_items, many=True).data
            subtotal = 0
            discount = 0

            for item in serializer_data:
                actual_price = item["retail_product_variation"]["price"]
                quantity = item["quantity"]

                subtotal += float(actual_price) * float(quantity)
                if item["retail_product_variation"]["discount"] and item["retail_product_variation"]["discount_amount"]:
                    discount = item["retail_product_variation"]["discount_amount"] * float(quantity)
            vendor_obj = Vendor.objects.get(id=vendor)
            vendor_name = VendorSerializer(vendor_obj).data['vendor_name']

            vendor_data.append({
                "vendor_id":vendor,
                "vendor_name":vendor_name,
                "items": serializer_data,
                "subtotal" : subtotal,
                "calculation_subtotal": subtotal,
                "discount": discount,
                "coupon_discount": 0,
                "coupon_details": None ,
                "vendor_coupon_discount": 0,
                "admin_coupon_discount": 0,
                "vendor_delivery_charge":0
            })
                    
        vendor_coupon_discount = 0
        admin_coupon_discount = 0
        
        # Handle coupon codes
        coupon_param = request.GET.getlist("coupon", "")
        vendor_param = request.GET.getlist("vendor_id", "")

        if coupon_param:
            coupon_param = request.GET.getlist("coupon", "")[0]

        if vendor_param:
            vendor_param = request.GET.getlist("vendor_id", "")[0]

        if coupon_param or vendor_param:
            coupon_codes = coupon_param.split(',')
            vendor_ids = vendor_param.split(',')

            vendor_ids.extend([None] * (len(coupon_codes) - len(vendor_ids)))

            for coupon_code, vendor_id in zip(coupon_codes, vendor_ids):
                try:
                    coupon = RetailCoupon.objects.filter(disabled=False).get(coupon_code=coupon_code)

                    if self.request.user.guest_user:
                        raise ValidationError({"message": "Guest Users cannot apply coupon.", "coupon": coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"  })
                    
                    if coupon_code and vendor_id and coupon.chowchow_coupon:
                        raise ValidationError({"message": f"{coupon_code} coupon not applicable here.", "coupon": coupon_code, "type": "admin"})
                    
                    if vendor_id:
                        try:
                            vendor = Vendor.objects.get(id=vendor_id)
                        except Vendor.DoesNotExist:
                            raise ValidationError({"message": f"Vendor with id {vendor_id} does not exist."})
                        
                        if vendor not in coupon.vendor.all():
                            raise ValidationError({"message": f"Coupon {coupon_code} does not belong to vendor {vendor_id}" , "coupon": coupon_code, "type": "retail" if vendor_id else "admin"})
                    
                    if not vendor_id and not coupon.chowchow_coupon:
                        raise ValidationError({"message": f" {coupon_code} coupon is not application here.", "coupon": coupon_code,"type": "retail" if vendor_id else "admin"})
                    
                except RetailCoupon.DoesNotExist:
                    raise ValidationError({"message": "The provided Coupon Code is invalid", "coupon": coupon_code,"type": "retail" if vendor_id else "admin"})
               
        chowchow_coupon = []

        if coupon_param:
            coupon_codes = coupon_param.split(',')
            applied_coupon_vendors = set()

            for code in coupon_codes:
                try:
                    coupon = RetailCoupon.objects.filter(disabled=False).get(coupon_code=code)

                    if coupon.start_date and coupon.start_date > current_time:
                        raise ValidationError({"message": f"Coupon Code {code} is not yet valid.", "coupon": coupon.coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"})
                    if coupon.end_date and coupon.end_date < current_time:
                        raise ValidationError({"message": f"Coupon Code {code} has expired.", "coupon": coupon.coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"})
                    
                    if coupon.usage >= coupon.coupon_usage_limitation:
                        raise ValidationError({'message': f'{coupon.coupons_title} coupon usage is over.', "coupon": coupon.coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"})
                    
                    user_coupon = self.request.user.user_profile.applied_coupon
                    user_coupon_count = 0
                    if user_coupon:
                        user_coupon = user_coupon.split(',')
                        if coupon.coupon_code in user_coupon:
                            user_coupon_count = user_coupon.count(coupon.coupon_code)

                    if user_coupon_count >= coupon.limitation_for_user:
                        raise ValidationError({'message': f'{coupon.coupons_title} coupon usage is over for you.', "coupon": coupon.coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"})
                    
                    for vendor in coupon.vendor.all():
                        if vendor.id in vendors:
                            
                            vendor_entry = next((v for v in vendor_data if v['vendor_id'] == vendor.id), None)
                            if not vendor_entry:
                                continue 

                            # if vendor.id in applied_coupon_vendors:
                            #     raise NotAcceptable({"message": f"Coupon Code for Vendor {vendor.vendor_name} applied twice"})

                            # User limitaion check garna baki cha
                        
                            # Apply coupon discount
                            if coupon.coupon_type == "Flat Discount":
                                discount_amount = coupon.discount_amount
                            elif coupon.coupon_type == "Percentage Off":
                                discount_amount = (vendor_entry['calculation_subtotal'] * coupon.discount_percentages / 100)

                            elif coupon.coupon_type == "Delivery Fee off":
                                # Handle delivery fee logic if applicable
                                # discount_amount = min(vendor_data[vendor.id]['subtotal'], coupon.discount_amount)
                                pass
                            else:
                                discount_amount = 0

                            if coupon.discount_type == "IN AMOUNT":
                                discount_amount = discount_amount
                            elif coupon.discount_type == "IN PERCENTAGE":
                                discount_amount = discount_amount

                            # Apply coupon limits
                            if vendor_entry['subtotal'] < coupon.minimum_spend_amount:
                                raise ValidationError({"message": f"Minimum spend amount for coupon Code {code} is not met for vendor {vendor.vendor_name}.", "coupon": coupon.coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"})
                            if coupon.maximum_redeem_amount and discount_amount > coupon.maximum_redeem_amount:
                                discount_amount = coupon.maximum_redeem_amount

                            if not coupon.chowchow_coupon:
                                vendor_entry['coupon_details'] = {
                                    'coupon_code' : coupon.coupon_code,
                                    'coupon_title' : coupon.coupons_title,
                                    'coupon_type' : coupon.coupon_type,
                                    'discount_amount' : discount_amount,
                                    'discount_percentages': coupon.discount_percentages,
                                }
                                vendor_coupon_discount = discount_amount
                            else:
                                chowchow_coupon.append({
                                    'vendor_id': vendor.id,
                                    'vendor_title': vendor.vendor_name,
                                    'coupon_code' : coupon.coupon_code,
                                    'coupon_title' : coupon.coupons_title,
                                    'coupon_type' : coupon.coupon_type,
                                    'discount_amount' : round(discount_amount, 2),
                                    'discount_percentages': coupon.discount_percentages,
                                })
                                admin_coupon_discount = discount_amount
                            vendor_entry['coupon_discount'] += discount_amount
                            vendor_entry['calculation_subtotal'] -= discount_amount
                            vendor_entry['vendor_coupon_discount'] = vendor_coupon_discount
                            vendor_entry['admin_coupon_discount'] = admin_coupon_discount

                            applied_coupon_vendors.add(vendor.id)
                        
                except RetailCoupon.DoesNotExist:
                    raise ValidationError({"message": f"The provided Coupon Code doesnot exists: {code}", "coupon": coupon.coupon_code, "type": "admin" if coupon.chowchow_coupon else "retail"})

        # Calculate totals and prepare the response
        total_subtotal = 0
        total_discount = 0
        total_coupon_discount = 0
        for data in vendor_data:
            for item in data['items']:
                if item['retail_product_variation']['discount']:
                    total_discount += item['retail_product_variation']['discount_amount'] * item['quantity']
            total_subtotal += data['subtotal']
            total_coupon_discount += data['coupon_discount']

        total_amount =  round(total_subtotal - total_discount - total_coupon_discount, 2)
        loyalty_discount_amount = 0
        if loyalty_code and loyalty:            
            if (loyalty.minimum_spend_amount) > total_amount:
                raise ValidationError({"message":"The minimum spend amount for loyalty is not fulfilled"})
            
            loyalty_discount_amount = (loyalty.discount_percentages / 100) * total_amount
            if loyalty_discount_amount > loyalty.maximum_redeem_amount:
                loyalty_discount_amount = loyalty.maximum_redeem_amount
                
            total_amount = total_amount - loyalty_discount_amount
        
         ##Delivery Charge
        vendor_delivery_charge = 0
        total_delivery_charge = 0

        location = request.GET.get("location", "")
        delivery_available=True

        if location:
            if location == "default address":
                user_location = request.user.user_profile

                user_lat = user_location.latitude
                user_long = user_location.longitude
            else:
                try:
                    user_location = UserLocation.objects.get(id=location)
                    user_lat = user_location.latitude
                    user_long = user_location.longitude
                except UserLocation.DoesNotExist:
                    raise ValidationError({'message':'Location doesnot exists.'})
        
        if user_lat and user_long:
            delivery_boundary_response = check_delivery_zone(user_lat, user_long)
            if delivery_boundary_response == False:
                delivery_available = False

            free_delivery = RetailFreeDelivery.objects.filter(
                Q(start_date__lte=current_time) & 
                Q(end_date__gte=current_time) & 
                Q(minimum_spend_amount__lte=total_subtotal),
                active=True
            ).first()

            if free_delivery:
                total_delivery_charge = 0
                vendor_delivery_charge = 0
            else:
                for vendor in vendors:
                    vendor_info = Vendor.objects.get(id=vendor)

                    vendor_lat = vendor_info.vendor_location_latitude
                    vendor_long = vendor_info.vendor_location_longitude

                    if not user_lat or not user_long:
                        raise ValidationError({"message": "User's latitude and longitude are required to calculate delivery charges."})

                    user_lat = float(user_lat)
                    user_long = float(user_long)

                    vendor_distance = haversine_distance(float(vendor_lat), float(vendor_long), user_lat, user_long)

                    delivery_charge_data = RetailDeliveryCharge.objects.filter(
                        min_distance__lte=vendor_distance,
                        max_distance__gte=vendor_distance,
                        status=True
                    ).first()
                    
                    if delivery_charge_data:
                        vendor_delivery_charge = RetailDeliveryChargeSerializer(delivery_charge_data).data['delivery_charge']

                        if vendor_delivery_charge:
                            data_entry = next((v for v in vendor_data if v['vendor_id'] == vendor_info.id), None)
                            data_entry['vendor_delivery_charge'] = vendor_delivery_charge
                        total_delivery_charge += vendor_delivery_charge
        
        # COD conditions
        cod_limit = 30000.0
        cod_allowed = True
        total = total_amount + float(total_delivery_charge)
        if total > cod_limit:
            cod_allowed = False
           
        cart_response_data = {
            "vendors": [
                {
                "vendor_id": values['vendor_id'],
                "vendor_name": values['vendor_name'],
                "vendor_coupon_details": values['coupon_details'],
                "items": values['items'],
                "subtotal": round(values['subtotal'], 2),

                "discount": round(sum(item['retail_product_variation'].get('discount_amount', 0) * item['quantity'] for item in values.get('items', [])), 2),
                "coupon-discount": round(values.get('coupon_discount', 0), 2),
                "total": round(values['subtotal'] - values['discount'] - values['coupon_discount'] + values['vendor_delivery_charge'], 2),
                "vendor_coupon_discount": round(values['vendor_coupon_discount'], 2),
                "admin_coupon_discount": round(values['admin_coupon_discount'], 2),
                "loyalty_discount_percent": loyalty.discount_percentages if loyalty else 0,
                "loyalty_discount_amount": round((loyalty.discount_percentages / 100) * round(values['subtotal'] - values['discount'] - values['coupon_discount'], 2), 2) if loyalty else 0,
                "vendor_delivery_charge": values['vendor_delivery_charge']
                } 
                for values in vendor_data
            ],
            "subtotal": round(total_subtotal, 2),
            "discount": round(total_discount, 2),
            "coupon-discount": round(total_coupon_discount, 2),
            "total": total_amount + float(total_delivery_charge),
            "loyalty-discount-amount": round(loyalty_discount_amount, 2), 
            "coupon_details": {
                "chowchow_coupon": chowchow_coupon if chowchow_coupon else None
            } if chowchow_coupon else None,
            "delivery_charge" : total_delivery_charge,
            "COD": cod_allowed,
            "delivery_available": delivery_available,
            "can_checkout" : True
        }
        
        place_order = bool(request.query_params.get("place_order",False))
        shared_wishlist = bool(request.query_params.get("shared_wishlist",False))
        method = request.query_params.get("method",None)

        if place_order:
            if shared_wishlist:
                ordered_cart = ordered_carts[0]
                shared_wishlist_cart_serializer = RetailCartSerializer(ordered_cart).data
                shared_wishlist_data = SharedRetailWishlist.objects.get(id=shared_wishlist_cart_serializer['shared_wishlist'])
                shared_wishlist_serializer = SharedRetailWishlistSerializer(shared_wishlist_data, context={'request':request}).data

                address = shared_wishlist_serializer['address']
                country = shared_wishlist_serializer['country']
                state = shared_wishlist_serializer['state']
                city = shared_wishlist_serializer['city']
                pin_code = shared_wishlist_serializer['pin_code']
                phone = shared_wishlist_serializer['phone_number']
                nation = shared_wishlist_serializer['nation']

            else:
                location = request.GET.get("location", "")
                if location == "default address":
                    user_location = request.user.user_profile

                    address = user_location.address
                    country = user_location.country
                    state = user_location.state
                    city = user_location.city
                    pin_code = user_location.pin_code
                    phone = user_location.phone_number
                    nation = user_location.nation
                else:
                    try:
                        user_location = UserLocation.objects.get(id=location)

                        address = user_location.address
                        country = user_location.country
                        state = user_location.state
                        city = user_location.city
                        pin_code = user_location.pin_code
                        phone = user_location.phone_number
                        nation = user_location.nation
                    except UserLocation.DoesNotExist:
                        raise ValidationError({'message':'Location doesnot exists.'})
                                
            if not( address and country and state and city and pin_code):
                raise ValidationError({"message":"Address details have not been filled"})
            
            if address==None or country==None or state==None or city==None or pin_code==None:
                raise ValidationError({"message":"Address details have not been filled"})
            
            total_tax = 0
            for data in cart_response_data['vendors']:
                for item in data['items']:
                    total_tax += (item['retail_product_variation']['tax_amount'] * item['quantity'])

            new_order = RetailOrder.objects.create(
                cart_data = (cart_response_data),

                user = request.user,
                payment = None,
                order_number = uuid.uuid4(),
                first_name = request.user.first_name,
                last_name = request.user.last_name,
                email = request.user.email,

                phone = phone,
                address = address,
                country = country,
                state = state,
                city = city,
                pin_code = pin_code,
                
                total = cart_response_data['total'],
                total_tax = round(total_tax, 2),

                delivery_charge = total_delivery_charge,
                # delivery_date = delivery_time,
                is_ordered = False,
                status = "New",

                loyalty_points_received = cart_response_data['total'],
                loyalty_program = loyalty if loyalty_code else None,

                nation = nation

            )
            new_order.vendors.set(vendors)
            new_order.carts.set(ordered_carts)

            for each_vendor in cart_response_data['vendors']:
                vendor_total_tax = 0
                for item in each_vendor['items']:
                    vendor_total_tax += item['retail_product_variation']['tax_amount'] * item['quantity']

                coupon_used = None
                if each_vendor['vendor_coupon_details']:
                    coupon_used = RetailCoupon.objects.filter(disabled=False).get(coupon_code=each_vendor['vendor_coupon_details']['coupon_code'])

                if cart_response_data['coupon_details']:
                    coupon_used = RetailCoupon.objects.filter(disabled=False).get(coupon_code=cart_response_data['coupon_details']['chowchow_coupon'][0]['coupon_code'])

                vendor_items = RetailVendorOrder.objects.create(
                    vendor = Vendor.objects.get(id=each_vendor['vendor_id']),
                    order = new_order,
                    coupon_used = coupon_used,
                    sub_total = each_vendor['subtotal'],
                    total_amount = each_vendor['total'],
                    total_discount_amount = each_vendor['discount'],
                    total_tax = round(vendor_total_tax, 2),
                    vendor_coupon_discount = each_vendor['vendor_coupon_discount'],
                    admin_coupon_discount = each_vendor['admin_coupon_discount'],
                    loyalty_discount_amount = each_vendor['loyalty_discount_amount'],
                    delivery_charge = each_vendor['vendor_delivery_charge']
                )
                for item in each_vendor['items']:

                    ordered_product = OrderedProduct.objects.create(
                        order = new_order,
                        product_variation = RetailProductsVariations.objects.get(id=item['retail_product_variation']['id']),
                        quantity = item['quantity'],
                        price = round(float(item['retail_product_variation']['price']) * float(item['quantity']), 2),
                        discount_amount = float(item['retail_product_variation']['discount_amount']) * float(item['quantity']) if item['retail_product_variation']['discount'] else 0,
                        discounted_amount = float(item['retail_product_variation']['discounted_amount']) * float(item['quantity']) if item['retail_product_variation']['discount'] else round(float(item['retail_product_variation']['price']) * float(item['quantity']), 2),
                        tax_rate = item['retail_product_variation']['tax_percentage'],
                        tax_exclusive_amount = round(float(item['retail_product_variation']['tax_exclusive_price']) * float(item['quantity']), 2),
                        vendor_order = vendor_items
                    )

                    try:
                        order_status = OrderStatus.objects.get(status_code='001')
                    except OrderStatus.DoesNotExist:
                        order_status = OrderStatus.objects.create(
                            status = "initial status",
                            status_code = "001"
                        )

                    ordered_product_status = OrderedProductStatus.objects.create(
                        ordered_product = ordered_product,
                        status = order_status,
                        created_by = request.user,
                    )
            
            if method == "Stripe":
                try:
                    session = stripe.checkout.Session.create(
                        ui_mode = 'embedded',
                        payment_method_types=['card'],
                        customer_email = request.user.email,
                        line_items=[
                            {
                                'price_data': {
                                    'currency': 'npr',
                                    'product_data': {
                                        'name': 'Total Cost',
                                        'description':'This is the total cost of your transaction'
                                    },
                                    'unit_amount': int((new_order.total)*100),
                                },
                                'quantity': 1,
                            }
                        ],
                        mode='payment',
                        return_url='https://dev.majjakodeals.com/retail-orders/confirm-retail-payment/' + f'?order_number={new_order.order_number}&method={method}&buy_now={buy_now}''&session_id={CHECKOUT_SESSION_ID}'
                    )

                except Exception as e:
                    raise e

                new_order.order_payment_code = session.client_secret
                new_order.save()

                return JsonResponse({"clientSecret":session.client_secret, "order_number":new_order.order_number})

            if method == "Cash On Delivery":
                try:
                    confirm_order = ConfirmRetailOrderView()
                    a = confirm_order.list(request, order_number=str(new_order.order_number), method=method, buy_now=buy_now)
                    return Response({"order_number":new_order.order_number}, status=status.HTTP_200_OK) 
                except Exception as e:
                    # print(e)
                    return redirect("https://majjakodeals.com/order-could-not-be-process")
            
            if method == "Esewa":
                url = settings.ESEWA_CONFIG['ESWEA_URL']

                transaction_uuid = str(new_order.order_number) + '-buy_now_' + buy_now
                product_code = "EPAYTEST"


                payload = {
                    "amount":str(int(new_order.total)),
                    "failure_url": f"https://{dev.majjakodeals.com}/retail-orders/cancel-retail-payment/"f'?order_number={new_order.order_number}&method={method}',
                    "product_delivery_charge": "0",
                    "product_service_charge": "0",
                    "product_code": product_code,
                    "signature": generate_esewa_signature(
                        secret_key= settings.ESEWA_CONFIG['SECRET_KEY'], 
                        total_amount=int(new_order.total), 
                        transaction_uuid=transaction_uuid, 
                        product_code=product_code,
                        ),
                    "signed_field_names": f"total_amount,transaction_uuid,product_code",
                    "success_url": f"https://{base_url}/retail-orders/confirm-retail-payment/",
                    "tax_amount": "0",
                    "total_amount": str(int(new_order.total)),
                    "transaction_uuid": str(transaction_uuid)
                    }


                return Response({
                    'esewa_url': url,
                    'payload' : payload
                })
        
        if cart_response_data['subtotal'] < 300:
            cart_response_data['can_checkout'] = False
            return Response(cart_response_data)

        return Response(cart_response_data)

from rest_framework import views
from django.core.cache import cache

class CurrencyExchangeRateView(views.APIView):
    def get(self, request, *args, **kwargs):

        cached_data = cache.get('currency_exchange_rate')
        if cached_data:
            return Response({"usd": cached_data})
        
        url = "https://v6.exchangerate-api.com/v6/f5f4cc786dea20eedbfe8d96/latest/NPR"

        response = requests.get(url)
        data = response.json()

        usd = data['conversion_rates']['USD']

        cache.set('currency_exchange_rate', usd, timeout=43200)

        return Response({"usd":usd})