from datetime import timedelta, datetime
from datetime import timezone as tz
import pytz
import uuid
import stripe
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from rest_framework.response import Response
from django.db.models import Q, F , Subquery , OuterRef, Value, IntegerField, CharField, DateTimeField
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from timezonefinder import TimezoneFinder
from dvls import settings
from marketplace.models import Cart, FoodCustomizations
from marketplace.serializers import CartAddonsSerializer, CartCalculationsSerializer, \
    CartItemsQuantitySerializer, CartSerializer, GetVendorsSerializer, UpdateCartItemsItems, UpdateQuantitySerializer, \
    UserCartsBreakdownSerializer, DiscountVendorSerializer
# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum
from rest_framework.exceptions import ValidationError, NotAcceptable
from menu.models import Customization, FoodItem

from offers.models import Coupons, LoyaltyPrograms
from orders.models import Order, OrderCustomization, OrderedFood, VendorsOrders
from vendor.models import Vendor

stripe.api_key = settings.STRIPE_API_KEY

class CartViewSet(ModelViewSet):
    queryset = Cart.objects.filter(active=True)
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fooditem']

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).filter(active=True)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    

    def update(self, request, *args, **kwargs):
        addons = request.data.pop("cart_addons","")
        create_addons = []
        for cart_addon in addons:
            if cart_addon.get("id", ""):
                cart_addon_update = FoodCustomizations.objects.get(id=cart_addon.get("id", ""))
                update_addons = CartAddonsSerializer(cart_addon_update, cart_addon, many=False)
                if update_addons.is_valid(raise_exception=True):
                    update_addons.save()
            else:
                create_addons.append(cart_addon)

        request.data['cart_addons'] = create_addons
        
        return super().update(request, *args, **kwargs)
    
class UpdateCartViewSet(ModelViewSet):
    queryset = FoodCustomizations.objects.all()
    serializer_class = UpdateCartItemsItems
    http_method_names = ['put']

    def get_queryset(self):
        return FoodCustomizations.objects.filter(cart__user = self.request.user).filter(cart__active = True)
    


class ClearCartViewSet(ModelViewSet):
    queryset = Cart.objects.filter(active=True)
    serializer_class = CartSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        query = Cart.objects.filter(user=self.request.user).filter(active=True)
        query.update(active=False)
        return Response({"message":"Cart emptied"}, status=status.HTTP_200_OK)


class UpdateCartQuantityViewSet(ModelViewSet):
    queryset = Cart.objects.filter(active=True)
    serializer_class = UpdateQuantitySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get','patch']

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).filter(active=True)
    

class ItemsQuantityInCart(ModelViewSet):
    queryset = Cart.objects.filter(active=True)
    serializer_class = CartItemsQuantitySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fooditem']

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).filter(active=True).distinct("fooditem")

class CartQuantityCalculation(ModelViewSet):
    queryset = Cart.objects.filter(active=True).distinct("fooditem")
    serializer_class = CartItemsQuantitySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fooditem']

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).filter(active=True).distinct("fooditem")
        


class CartBreakDownViewSet(ModelViewSet):
    queryset = Cart.objects.filter(active=True)
    serializer_class = UserCartsBreakdownSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fooditem']

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).filter(active=True)
        


class CartItemSCalculationViewSet(ModelViewSet):
    queryset = Cart.objects.filter(active=True)
    serializer_class = CartCalculationsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fooditem']

    def get_queryset(self):
        delivery_time = self.kwargs.get("delivery_time","")
        current_time = timezone.now()
        if delivery_time:
            if timedelta(delivery_time ) > current_time:
                return Cart.objects.filter(user=self.request.user).filter(active=True)
        return Cart.objects.filter(user=self.request.user).filter(active=True)
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_local_time(self, latitude, longitude):
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        if timezone_str:
            timezone = pytz.timezone(timezone_str)
            local_time = datetime.now(timezone)
            return local_time
        else:
            return None
    
    def list(self, request, *args, **kwargs):
        delivery_time =request.GET.get("delivery_time", "")
        loyalty_code =request.GET.get("loyalty_code", "")

        if loyalty_code:
            try:
                loyalty = LoyaltyPrograms.objects.get(program_code = loyalty_code)
            except LoyaltyPrograms.DoesNotExist:
                raise ValidationError({"message":"The loyalty program does not exist"})

        tips = request.query_params.get("tip","0")
        if tips == '':
            tips = "0"
        place_order = bool(request.query_params.get("place_order",False))

        try:
            tips = float(tips)
        except ValueError:
            raise ValidationError({"message":"The provided tip is not a  number"})

        current_time = timezone.now()

        weeK_day = current_time.weekday()

        if delivery_time:
            try:
                delivery_timeline = datetime.strptime(delivery_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError as e:
                raise ValueError({"message":"The delivery time doesnot match this format %Y-%m-%dT%H:%M:%S.%fZ 2"})
            if delivery_timeline.replace(tzinfo=tz.utc) < current_time:
                raise ValidationError({"message":"delivery time provided is older then current time"})
        else:
            delivery_time=current_time + timedelta(hours=4)
        coupon = request.GET.get("coupon","")


        vendors_list = Cart.objects.filter(user = request.user, active=True) #.values_list("fooditem__vendor", flat=True)
        for each_item in vendors_list:

            time_in_vendor = self.get_local_time(float(each_item.fooditem.vendor.vendor_location_latitude) , float(each_item.fooditem.vendor.vendor_location_longitude))
            food_item = each_item.fooditem
            if food_item.hours_schedule:
                if time_in_vendor.time() > food_item.hours_schedule.starting_hours and time_in_vendor.time() < food_item.hours_schedule.ending_hours and weeK_day in food_item.hours_schedule.week_days:
                    continue
                else:
                    vendors_list = vendors_list.exclude(id=each_item.id)
            elif food_item.vendor_categories.hours_schedule:
                if time_in_vendor > food_item.vendor_categories.hours_schedule.starting_hours and time_in_vendor < food_item.vendor_categories.hours_schedule.ending_hours and weeK_day in food_item.vendor_categories.hours_schedule.week_days:
                    continue
                else:
                    vendors_list = vendors_list.exclude(id=each_item.id)
            #elif food_item.vendor_categories.department.hours_schedule:
                #if time_in_vendor > food_item.vendor_categories.department.hours_schedule.starting_hours and time_in_vendor < food_item.vendor_categories.department.hours_schedule.ending_hours and weeK_day in food_item.vendor_categories.department.hours_schedule.week_days:
                 #   continue
                #else:
                   # vendors_list = vendors_list.exclude(id=each_item.id)
            else:
                continue
        
        vendors_list = vendors_list.values_list("fooditem__vendor", flat=True)

        # Calculating the authenticity of the coupons
        coupon_values = []
        coupon_vendors = []
        current_value = ""

        for element in coupon:
            if element != ",":
                current_value += element
            else:
                coupon_values.append(current_value)
                try:
                    coupon_obj = Coupons.objects.get(coupon_code = current_value)
                    if coupon_obj.vendor.id in coupon_vendors:
                        raise NotAcceptable({"message":f"Coupon Code for Vendor {coupon_obj.vendor.vendor_name} applied twice"})
                    
                    if coupon_obj.vendor.id not in vendors_list:
                        raise ValidationError({"message":f"The coupon code {coupon_obj.coupon_code}'s vendor is not in cart" })

                    coupon_vendors.append(coupon_obj.vendor.id)
                    #TODO
                    '''
                    Verify if the user had already used the coupon for the vendor 
                    '''
                except Coupons.DoesNotExist:
                    raise ValidationError({"message":f"The provided Coupon Code does not exist {current_value}"})
                current_value = ""
        coupon_details = Coupons.objects.filter(coupon_code__in = coupon_values)

        vendor_food_item = Cart.objects.filter(fooditem__vendor=OuterRef('pk'))
        cart_vendors = Cart.objects.filter(user=request.user, active=True).values_list('fooditem__vendor', flat=True).distinct()

        vendor = Vendor.objects.filter(id__in = cart_vendors)
        vendor.annotate(
            pri = F('id')
        )

        if coupon_details:
            vendor = vendor.annotate(
                coupons_offer =Subquery(
                    Coupons.objects.filter(coupon_code__in = coupon_values).filter(vendor_id=OuterRef('pk')).values('coupon_code')[:1])
                    )

        else:
            vendor = vendor.annotate(coupons_offer=Value(""))
        if delivery_time:
            vendor = vendor.annotate(delivery_time=Value(delivery_time, output_field=DateTimeField()))
        else:
            vendor = vendor.annotate(delivery_time=Value(current_time + timedelta(hours=4), output_field=DateTimeField()))

        data = GetVendorsSerializer({'vendors':vendor}, context={'request':self.request}, many=False).data

        if place_order:
            """
            TODO Add a place order
            TODO The order is created now for addons and vendor details
            """
            address =request.GET.get("address", "")
            country =request.GET.get("country", "")
            state =request.GET.get("state", "")
            city =request.GET.get("city", "")
            pin_code =request.GET.get("pin_code", "")
            
            if not( address and country and state and city and pin_code):
                raise ValidationError({"message":"address details have not been filled"})

            new_order = Order.objects.create(
                user = request.user,
                payment = None,
                order_number = uuid.uuid4(),
                first_name = request.user.first_name,
                last_name = request.user.last_name,
                phone = request.user.phone_number,
                email = request.user.email,
                loyalty_program = loyalty if loyalty_code else None,

                address = address,
                country = country,
                state = state,
                city = city,
                pin_code = pin_code,
                
                total = data['total_amount'],
                total_tax = data['total_tax'],

                delivery_charge = 0,
                tip = data['tip'],
                delivery_date = delivery_time,
                is_ordered = False,
                created_at = timezone.now(),
                status = "New",
                updated_at = timezone.now()
            )
            for each_vendor in data['vendors']:
                item = {}

                vendor_items = VendorsOrders.objects.create(
                    vendor = Vendor.objects.get(id=each_vendor['id']),
                    order = new_order,
                    coupon_used = Coupons.objects.get(coupon_code=each_vendor['coupons_offer']) if each_vendor['coupons_offer'] else None,
                    total_amount = each_vendor['total_amount'],
                    discounted_amount = each_vendor['discounted_price'],
                    addons_cost = each_vendor['addons_cost'],
                    total_tax = each_vendor['total_tax']
                )



                ordered_food = [{"orders":
                            OrderedFood.objects.create(
                            order = new_order,
                            user = request.user,
                            food_item = FoodItem.objects.get(id= each_item['fooditem']['id']),
                            quantity = each_item['quantity'],
                            price = each_item['discounted_amount'],
                            created_at = timezone.now(),
                            updated_at = timezone.now(),
                            amount = each_item['actual_amount'],
                            vendor_order = vendor_items,
                            cart_id = each_item['cart_id'],
                            receiver_name = each_item['receiver_name']

                            ), #if not each_item['cart_addons'] else None ,
                            
                            "addons": [OrderCustomization.objects.create(
                                customization = Customization.objects.get(id=each_customization['customization_set']['id']),
                                amount = each_customization['customization_set']['price'],
                                order_customization = new_order,
                                quantity = each_customization['quantity'],

                                food = OrderedFood.objects.create(
                                order = new_order,
                                user = request.user,
                                food_item = FoodItem.objects.get(id= each_item['fooditem']['id']),
                                quantity = each_item['quantity'],
                                price = each_item['discounted_amount'],
                                created_at = timezone.now(),
                                updated_at = timezone.now(),
                                amount = each_item['actual_amount'],
                                vendor_order = vendor_items,
                                cart_id = each_item['cart_id'],
                                receiver_name = each_item['receiver_name']


            ) if not OrderedFood.objects.filter(cart_id = each_item['cart_id']).exists() else OrderedFood.objects.get(cart_id=each_item['cart_id'])

                            ) for each_customization in each_item['cart_addons']]
                            } 
                            for each_item in each_vendor['food_items']
                            ]
                
            cart_items = Cart.objects.filter(user=request.user)

            cart_items.update(active=False)

            try:
                session = stripe.checkout.Session.create(
                    ui_mode = 'embedded',
                    payment_method_types=['card'],
                    customer_email = request.user.email,
                    line_items=[{
                        'price_data': {
                        'currency': 'usd',
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
                    return_url='https://dev.majjakodeals.com/orders/confirm_payment/' + f'?order_number={new_order.order_number}''&session_id={CHECKOUT_SESSION_ID}',
                    # return_url=f'https://dev.chowchowexpress.com/orders/confirm_payment/?order_number={new_order.order_number}&session_id={session.id}',

                    # return_url='http://localhost:3000/order_confirmation/' + f'?order_number={new_order.order_number}''&session_id={CHECKOUT_SESSION_ID}',

                )

            except Exception as e:
                raise e

            new_order.order_payment_code = session.client_secret
            new_order.save()

            return JsonResponse({"clientSecret":session.client_secret, "order_number":new_order.order_number})
        return Response(data)



