import base64
import decimal
import json
from django.shortcuts import render
import requests
from rest_framework import views
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from rest_framework.response import Response 
from utils.mail import send_mail_using_graph
from django.template.loader import render_to_string

from retail_offers.models import RetailCoupon, RetailLoyaltyPrograms
from retail_orders.filters import OrderedProductFilter
from user.models import UserProfile
from utils.permissions_override import IsVendor, IsSuperAdmin

from retail_marketplace.models import RetailCart

from rest_framework.pagination import PageNumberPagination

from .models import OrderStatus, OrderedProduct, OrderedProductStatus, RetailOrder, RetailPayment, RetailPaymentInfo, RetailVendorOrder
from .serializers import AdminOrderStatusSerializer, AdminOrderedProductStatusSerializer, AdminRetailOrderedProductSerializer, DetailVendorOrderSerializer, OrderedProductStatusSerializer, RetailOrderedProductSerializer, RetailOrdersSerializer, RetailPaymentsSerializer, RetailVendorOrdersSerializer


import stripe
from dvls import settings

import uuid
import time
# Create your views here.

domain = settings.DOMAIN

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        page = request.query_params.get('page', None)

        if page is None:
            return None

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if self.page is None:
            return Response({'results': data})
        
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })
    

class ConfirmRetailOrderView(ReadOnlyModelViewSet):
    queryset = RetailPayment.objects.all()
    serializer_class = RetailOrdersSerializer

    def list(self, request, *args, **kwargs):
        order_number = kwargs.get('order_number') or request.query_params.get('order_number')
        method = kwargs.get('method') or request.query_params.get('method')
        buy_now = kwargs.get('buy_now') or request.query_params.get('buy_now')

        if method not in ['Stripe', 'Cash On Delivery']:
            method = 'Esewa'

        payment=None
        if method == 'Stripe':
            try:
                order = RetailOrder.objects.get(order_number=order_number)
            except RetailOrder.DoesNotExist:
                raise ValidationError({"message":"The order doesnot exist"})
            
            session_id = request.query_params.get('session_id')

            stripe.api_key = settings.STRIPE_API_KEY
            try:
                session =stripe.checkout.Session.retrieve(
                session_id, expand=['payment_intent.payment_method']
                )
            except Exception as e:
                raise ValidationError({"message":str(e)})
            
            if RetailPayment.objects.filter(transaction_id = session_id).exists():
                raise ValidationError({"message":"The session of stripe is not accurate"})

            payment = RetailPayment.objects.create(
                user = order.user,
                transaction_id = session.id,
                payment_method = method,
                amount = session.amount_subtotal / 100,
                status = session.status,
                created_at = timezone.now()
            )
            RetailPaymentInfo.objects.create(
                payment = payment,
                session_id = session.id,
                payment_intent_id = session.payment_intent.id,
                card_last4 = session.payment_intent.payment_method.card.last4,
                card_brand=session.payment_intent.payment_method.card.brand,
                customer_name= session.customer_details.name,
                customer_email=session.customer_details.email,
                customer_phone=session.customer_details.phone,
            )
        elif method == 'Cash On Delivery':

            try:
                order = RetailOrder.objects.get(order_number=order_number)
            except RetailOrder.DoesNotExist:
                raise ValidationError({"message":"The order doesnot exist"})
            
            payment = RetailPayment.objects.create(
                user = order.user,
                transaction_id = f"{int(time.time())}_{uuid.uuid4()}",
                payment_method = method,
                amount = order.total,
                status = "new",
                created_at = timezone.now()
            )
        elif method == 'Esewa':
            response_base64 = request.GET.get('data', None)
            response_decoded = base64.b64decode(response_base64).decode('utf-8')
            response_params = json.loads(response_decoded)

            total_amount = response_params.get('total_amount', None)
            product_code =  response_params.get('product_code', None)

            transaction_uuid =  response_params.get('transaction_uuid', None)
            buy_now = transaction_uuid.split('_')[-1]
            transaction_uuid = transaction_uuid.split("-buy_now")[0]

            order_number = transaction_uuid
            try:
                order = RetailOrder.objects.get(order_number=order_number)
            except RetailOrder.DoesNotExist:
                raise ValidationError({"message":"The order doesnot exist"})


            status_check_url =  f"{settings.ESEWA_CONFIG['STATUS_CHECK_URL']}?product_code={product_code}&total_amount={total_amount}&transaction_uuid={transaction_uuid}"

            response = requests.get(status_check_url)
            response = response.json()
            if response.get("status") == "COMPLETE":
                payment = RetailPayment.objects.create(
                    user = order.user,
                    transaction_id = transaction_uuid,
                    payment_method = method,
                    amount = total_amount,
                    status = "COMPLETE",
                    created_at = timezone.now()
                )

            # if response.get("status") == "CANCELED":
            #     order = RetailOrder.objects.get(order_number=order_number)
            #     order.status = "Cancelled"
            #     order.save()
            #     return Response({"message":"Your order has been cancelled."})
        else:
            raise ValidationError({"message":"The payment is not completed"})

        order = RetailOrder.objects.get(order_number=order_number)

        if order.payment == None:
            order.payment = payment
            order.is_ordered = True
            order.payment_method = method
            order.save()

            if buy_now:
                cart_items = RetailCart.objects.filter(user=order.user, buy_now=True)
                cart_items.update(active=False)
            else:
                cart_items = RetailCart.objects.filter(user=order.user)
                cart_items.update(active=False)

            user_profile = UserProfile.objects.get(user=order.user)
            if order.loyalty_program:
                loyalty = RetailLoyaltyPrograms.objects.get(id=order.loyalty_program.id)
                user_profile.loyalty_points -= loyalty.no_of_points
                user_profile.save()

            user_profile.loyalty_points += order.cart_data['subtotal']
            user_profile.save()
            
            user_applied_coupon_list = []
            for data in order.retail_order_vendor.all():
                if data.coupon_used: 
                    coupon = data.coupon_used
                    coupon = RetailCoupon.objects.filter(coupon_code=coupon.coupon_code).first()
                    coupon.usage += 1
                    coupon.save()

                    user_applied_coupon_list.append(coupon.coupon_code)

            if user_applied_coupon_list:
                user_applied_coupon = ",".join(user_applied_coupon_list)
                
                if user_profile.applied_coupon:
                    user_profile.applied_coupon += f",{user_applied_coupon}"
                else:
                    user_profile.applied_coupon = user_applied_coupon

                user_profile.save()
            
            # Email to customer
            ordered_products = OrderedProduct.objects.filter(order=order)
            
            mail_subject = 'Thank you for ordering with us.'
            mail_template = 'retail_orders/order_confirmation.html'
            # order_number = order.order_number
            order_no = order.order_number.split('-')[0]
            #slice the first part only of order
            # number of format 12hdh234-jdsfj234-wsdfd2-sdf to 12hdh234
            # order_number = order_number.split('-')[0]

            context = {
                "to_email" : order.email,
                "order" : order,
                "order_no" : order_no,
                "ordered_products" : ordered_products,
                "subtotal" :   order.cart_data['subtotal'],
                "coupon_discount" : order.cart_data['coupon-discount'],
                "loyalty_discount" : order.cart_data['loyalty-discount-amount'],
                "discount" : order.cart_data['discount']
            }

            send_mail_using_graph(
                receiver_email=context['to_email'], 
                subject=mail_subject, 
                message_text=render_to_string(mail_template, context)
            )

            # Email to vendors
            vendor_orders = RetailVendorOrder.objects.filter(order=order)
            for each_vendor in vendor_orders:
                ordered_products = OrderedProduct.objects.filter(order=order, vendor_order=each_vendor)

                mail_subject = 'Thank you for ordering with us.'
                mail_template = 'retail_orders/new_order_received.html'

                coupon_discount =  float(each_vendor.vendor_coupon_discount) + float(each_vendor.admin_coupon_discount)
                order_no = order.order_number.split('-')[0]

                context = {
                    "to_email" : each_vendor.vendor.user.email,
                    "order_no" : order_no,
                    "order" : order,
                    "vendor_order" : each_vendor,
                    "ordered_products" : ordered_products,
                    "coupon_discount" : round(coupon_discount, 2)
                }

                send_mail_using_graph(
                    receiver_email=context['to_email'], 
                    subject=mail_subject, 
                    message_text=render_to_string(mail_template, context)
                )
            
            # return Response({"order_number":order_number}, status=status.HTTP_200_OK) 
            return redirect(f"https://majjakodeals.com/retail-order-confirmation?order_number="+order_number)
        else:
            raise ValidationError({"message":"The payment for the order is already completed"})

class CancelRetailOrderView(ReadOnlyModelViewSet):
    queryset = RetailPayment.objects.all()
    serializer_class = RetailOrdersSerializer

    def list(self, request, *args, **kwargs):
        order_number = kwargs.get('order_number') or request.query_params.get('order_number')
        method = kwargs.get('method') or request.query_params.get('method')

        order = RetailOrder.objects.get(order_number=order_number)
        order.status = "Cancelled"
        order.save()
        
        return redirect("https://majjakodeals.com/info/payment-error")
    
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework import response
class RetailOrdersViewSet(ModelViewSet):
    queryset = RetailOrder.objects.all()
    serializer_class = RetailOrdersSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['order_number']
    permission_classes = [IsAuthenticated]
    search_fields = ['order_number']
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        if request.query_params.get('order_number'):
            try:
                queryset =  RetailOrder.objects.get(order_number = request.query_params.get('order_number'))
            except:
                raise ValidationError({"message":"The order number doesnot exist"})
            serializer = RetailOrdersSerializer(queryset,many=False ,context={"request":request}).data
            return response.Response(serializer, status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)

class UserRetailOrdersViewSet(ModelViewSet):
    queryset = RetailOrder.objects.all()
    serializer_class = RetailOrdersSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['order_number']
    permission_classes = [IsAuthenticated]
    search_fields = ['order_number']
    pagination_class = StandardResultsSetPagination
    http_method_names = ['get']

    def get_queryset(self):
        return RetailOrder.objects.filter(user=self.request.user).order_by('-created_at')

class RetailPaymentViewSet(ModelViewSet):
    queryset = RetailPayment.objects.all()
    serializer_class = RetailPaymentsSerializer

class RetailVendorOrdersViewSet(ModelViewSet):
    queryset = RetailOrder.objects.all()
    serializer_class = DetailVendorOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['order_number']
    search_fields = ['order_number']
    permission_classes = [IsVendor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return RetailOrder.objects.filter(retail_order_vendor__vendor__user = self.request.user)
    
    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()
        if 'order_number' in self.request.query_params:
            order = RetailOrder.objects.filter(retail_order_vendor__vendor__user = self.request.user).filter(order_number=self.request.query_params['order_number']).first()
            if not order:
                return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response( DetailVendorOrderSerializer(order,  context={"request":request}).data )
        
        queryset = self.filter_queryset(self.get_queryset())
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrderedProductViewSet(ModelViewSet):
    queryset = OrderedProduct.objects.all()
    serializer_class = RetailOrderedProductSerializer
    http_method_names =['get']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['order']
    search_fields  = ['product_variation__sku', 'order', 'product_variation__product__name']
    permission_classes = [IsVendor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return OrderedProduct.objects.filter(product_variation__product__vendor__user = self.request.user)

    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()

        orders = RetailOrder.objects.filter(vendors__user=request.user)

        if 'order' in self.request.query_params:
            order = self.request.query_params['order']
            try:
                order = RetailOrder.objects.get(id=order)
                ordered_product = OrderedProduct.objects.filter(order=order.id).filter(product_variation__product__vendor__user=request.user)
                serializer = RetailOrderedProductSerializer(ordered_product, many=True, context={"request":self.request})
                return response.Response(serializer.data)
            except RetailOrder.DoesNotExist:
                raise ValidationError({"message":"Invalid Order"})
        
        paginated_orders = paginator.paginate_queryset(orders, request, view=self)
        grouped_serializer_data = []

        if paginated_orders is None:
            paginated_orders = orders
            for order in paginated_orders:
                ordered_products = OrderedProduct.objects.filter(order=order.id).filter(product_variation__product__vendor__user=request.user)
                grouped_serializer_data.append({
                    "order_id":order.id, 
                    "order_number":order.order_number, 
                    "ordered_products":RetailOrderedProductSerializer(ordered_products, many=True, context={"request":self.request}).data
                    })
            return Response(grouped_serializer_data)

        for order in paginated_orders:
            ordered_products = OrderedProduct.objects.filter(order=order.id).filter(product_variation__product__vendor__user=request.user)
            grouped_serializer_data.append({
                "order_id":order.id, 
                "order_number":order.order_number, 
                "ordered_products":RetailOrderedProductSerializer(ordered_products, many=True, context={"request":self.request}).data
                })

        return paginator.get_paginated_response(grouped_serializer_data)



class OrderedProductStatusViewSet(ModelViewSet):
    queryset = OrderedProductStatus.objects.all()
    serializer_class = OrderedProductStatusSerializer


class UserOrderedProductViewSet(ModelViewSet):
    queryset = OrderedProduct.objects.all()
    serializer_class = RetailOrderedProductSerializer
    http_method_names =['get']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields  = ['product_variation__sku', 'order', 'product_variation__product__name', 'order__order_number']
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['order', 'ordered_product_status']

    def get_queryset(self):
        return OrderedProduct.objects.filter(order__user = self.request.user)

class GroupedUserOrderedProductViewSet(ModelViewSet):
    queryset = OrderedProduct.objects.all()
    serializer_class = RetailOrderedProductSerializer
    http_method_names =['get']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields  = ['product_variation__sku', 'order', 'product_variation__product__name', 'order__order_number']
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['order', 'ordered_product_status']

    def get_queryset(self):
        return OrderedProduct.objects.filter(order__user = self.request.user)
    
    def list(self, request, *args, **kwargs):
        grouped_serializer_data = []
        paginator = StandardResultsSetPagination()
        orders = RetailOrder.objects.filter(user=request.user).order_by('-created_at')
        if 'order' in self.request.query_params:
            order = self.request.query_params['order']
            try:
                order = RetailOrder.objects.get(id=order)
                ordered_product = OrderedProduct.objects.order_by('-created_at').filter(order=order.id).filter(order__user = self.request.user)
                grouped_serializer_data.append({
                    "order_id":order.id, 
                    "order_number":order.order_number, 
                    "ordered_products":RetailOrderedProductSerializer(ordered_product, many=True, context={"request":self.request}).data
                    })
                return response.Response(grouped_serializer_data)
            except RetailOrder.DoesNotExist:
                raise ValidationError({"message":"Invalid Order"})
            
        if 'order_status' in self.request.query_params:
            order_status = self.request.query_params['order_status']
            orders = orders.filter(status__iexact=order_status)
        
        paginated_orders = paginator.paginate_queryset(orders, request, view=self)
        if paginated_orders is None:
            paginated_orders = orders
            for order in paginated_orders:
                ordered_products = OrderedProduct.objects.order_by('-created_at').filter(order=order.id).filter(order__user = self.request.user)
                grouped_serializer_data.append({
                    "order_id":order.id, 
                    "order_number":order.order_number, 
                    "ordered_products":RetailOrderedProductSerializer(ordered_products, many=True, context={"request":self.request}).data
                    })
            return Response(grouped_serializer_data)

        for order in paginated_orders:
            ordered_products = OrderedProduct.objects.order_by('-created_at').filter(order=order.id).filter(order__user = self.request.user)
            grouped_serializer_data.append({
                "order_id":order.id, 
                "order_number":order.order_number, 
                "ordered_products":RetailOrderedProductSerializer(ordered_products, many=True, context={"request":self.request}).data
                })
        return paginator.get_paginated_response(grouped_serializer_data)


# ADMIN Viewset
    
class AdminOrderStatusVIewSet(ModelViewSet):
    queryset = OrderStatus.objects.all()
    serializer_class = AdminOrderStatusSerializer
    permission_classes = [IsSuperAdmin]

class AdminOrderedProductStatusViewSet(ModelViewSet):
    queryset = OrderedProductStatus.objects.order_by('-created_at')
    serializer_class = AdminOrderedProductStatusSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['ordered_product']
    search_fields = ['ordered_product__order__order_number']
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()
        if 'ordered_product' in self.request.query_params:
            ordered_product = self.request.query_params['ordered_product']

            ordered_product = OrderedProduct.objects.get(id=ordered_product)
            ordered_product.seen = True
            ordered_product.save()

            status = OrderedProductStatus.objects.filter(ordered_product=ordered_product.id)
            serializer = AdminOrderedProductStatusSerializer(
                status, many=True, context={'request': self.request}
            )
            return Response(serializer.data)

        queryset = self.filter_queryset(self.get_queryset())
        unseen_count = queryset.filter(ordered_product__seen=False).count()
        
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            paginated_response.data['unseen_count'] = unseen_count
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'unseen_count': unseen_count,
            'results': serializer.data
        })


class AdminOrderedProductViewSet(ModelViewSet):
    queryset = OrderedProduct.objects.all()
    serializer_class = AdminRetailOrderedProductSerializer
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = OrderedProductFilter
    search_fields = ['product_variation__product__name', 'order__order_number', 'order__first_name', 'order__last_name' ]
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.queryset.order_by('-created_at')
    
    # def retrieve(self, request, *args, **kwargs):
    #     review_instance = self.get_object()
    #     review_instance.seen = True
    #     review_instance.save()
    #     serializer = self.get_serializer(review_instance)
    #     return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()

        queryset = self.filter_queryset(self.get_queryset())
        unseen_count = queryset.filter(seen=False).count()

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            paginated_response.data['unseen_count'] = unseen_count
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'unseen_count': unseen_count,
            'results': serializer.data
        })


class AdminOrderedProductUnseenCountView(views.APIView):
    def get(self, request):
        unseen_count = OrderedProduct.objects.filter(seen=False).count()
        return Response({"unseen_count": unseen_count})



#Analytics
class AnalyticsView(views.APIView):
    def get_ordered_products(self, vendor=None):
        if vendor:
            return OrderedProduct.objects.filter(vendor_order__vendor=vendor)
        return OrderedProduct.objects.all()
    
    def get(self, request):
        year = request.query_params.get('year', None)
        month = request.query_params.get('month', None)
        week = request.query_params.get('week', None)
        date = request.query_params.get('date', None)

        vendor = request.query_params.get('vendor', None)

        total_sales = 0
        total_tax = 0
        discount = 0
        vendor_coupon_discount = 0
        admin_coupon_discount = 0
        delivery_charge = 0

        ordered_products = self.get_ordered_products(vendor)
        if ordered_products:
            for product in ordered_products:
                total_sales += product.price
                tax_rate = product.tax_rate
                price = product.price
                tax_amount = price * (float(tax_rate) /100)
                total_tax += tax_amount
        
            vendor_orders = ordered_products.values('vendor_order').distinct()
            for vendor_order in vendor_orders:
                order = RetailVendorOrder.objects.get(id=vendor_order['vendor_order'])
                discount += order.total_discount_amount
                vendor_coupon_discount += order.vendor_coupon_discount
                admin_coupon_discount += order.admin_coupon_discount
                delivery_charge += order.delivery_charge
        

        if date:
            total_sales = 0
            total_tax = 0
            discount = 0
            vendor_coupon_discount = 0
            admin_coupon_discount = 0
            delivery_charge = 0
            
            ordered_products = self.get_ordered_products(vendor).filter(created_at__date=date)
            if ordered_products:
                for product in ordered_products:
                    total_sales += product.price
                    tax_rate = product.tax_rate
                    price = product.price
                    tax_amount = price * (float(tax_rate) /100)
                    total_tax += tax_amount

                vendor_orders = ordered_products.values('vendor_order').distinct()
                for vendor_order in vendor_orders:
                    order = RetailVendorOrder.objects.get(id=vendor_order['vendor_order'])
                    discount += order.total_discount_amount
                    vendor_coupon_discount += order.vendor_coupon_discount
                    admin_coupon_discount += order.admin_coupon_discount
                    delivery_charge += order.delivery_charge
            return Response({
                 "total_sales":round(total_sales, 2),
                'total_order_count':ordered_products.count(), 
                "total_tax":round(total_tax, 2), 
                "discount": round(discount, 2), 
                "vendor_coupon_discount": round(vendor_coupon_discount, 2),
                "admin_coupon_discount": round(admin_coupon_discount, 2),
                "delivery_charge": round(delivery_charge, 2)
              }) 


        if year and month and week:
            total_sales = 0
            total_tax = 0
            total_sales, count, total_tax, discount, vendor_coupon_discount, admin_coupon_discount, delivery_charge  = self.filter_weekly(year, month, week, vendor)
            return Response({
                 "total_sales":round(total_sales, 2),
                "total_order_count": count,
                "total_tax":round(total_tax, 2), 
                "discount": round(discount, 2), 
                "vendor_coupon_discount": round(vendor_coupon_discount, 2),
                "admin_coupon_discount": round(admin_coupon_discount, 2),
                "delivery_charge": round(delivery_charge, 2)
            }) 
        
        if year and month:
            total_sales = 0
            total_tax = 0
            total_sales, count, total_tax, discount, vendor_coupon_discount, admin_coupon_discount, delivery_charge = self.filter_monthly(year, month, vendor)
            return Response({
                "total_sales":round(total_sales, 2),
                "total_order_count": count,
                "total_tax":round(total_tax, 2), 
                "discount": round(discount, 2), 
                "vendor_coupon_discount": round(vendor_coupon_discount, 2),
                "admin_coupon_discount": round(admin_coupon_discount, 2),
                "delivery_charge": round(delivery_charge, 2)
            }) 

        if year:
            total_sales = 0
            total_tax = 0
            total_sales, count, total_tax, discount, vendor_coupon_discount, admin_coupon_discount, delivery_charge  = self.filter_year(year, vendor) 
            return Response({
                "total_sales":round(total_sales, 2),
                "total_order_count": count,
                "total_tax":round(total_tax, 2), 
                "discount": round(discount, 2), 
                "vendor_coupon_discount": round(vendor_coupon_discount, 2),
                "admin_coupon_discount": round(admin_coupon_discount, 2),
                "delivery_charge": round(delivery_charge, 2)
            }) 
        
        return Response({
            "total_sales":round(total_sales, 2),
            'total_order_count':ordered_products.count(), 
            "total_tax":round(total_tax, 2), 
            "discount": round(discount, 2), 
            "vendor_coupon_discount": round(vendor_coupon_discount, 2),
            "admin_coupon_discount": round(admin_coupon_discount, 2),
            "delivery_charge": round(delivery_charge, 2)
        })

    def filter_year(self, year, vendor): 
        total_sales = 0
        total_tax = 0
        discount = 0
        vendor_coupon_discount = 0
        admin_coupon_discount = 0
        delivery_charge = 0

        if year:
            ordered_products = self.get_ordered_products(vendor).filter(created_at__year=year)
            if ordered_products:
                for product in ordered_products:
                    total_sales += product.price
                    tax_rate = product.tax_rate
                    price = product.price
                    tax_amount = price * (float(tax_rate) /100)
                    total_tax += tax_amount
            
                vendor_orders = ordered_products.values('vendor_order').distinct()
                for vendor_order in vendor_orders:
                    order = RetailVendorOrder.objects.get(id=vendor_order['vendor_order'])
                    discount += order.total_discount_amount
                    vendor_coupon_discount += order.vendor_coupon_discount
                    admin_coupon_discount += order.admin_coupon_discount
                    delivery_charge += order.delivery_charge

        return (total_sales, ordered_products.count(), total_tax, discount, vendor_coupon_discount, admin_coupon_discount, delivery_charge)
    
    def filter_monthly(self, year, month, vendor):
        total_sales = 0
        total_tax = 0
        discount = 0
        vendor_coupon_discount = 0
        admin_coupon_discount = 0
        delivery_charge = 0

        if month and 1 <= int(month) <= 12:
            if year:
                ordered_products = self.get_ordered_products(vendor).filter(created_at__year=year, created_at__month=month)
                if ordered_products:
                    for product in ordered_products:
                        total_sales += product.price
                        tax_rate = product.tax_rate
                        price = product.price
                        tax_amount = price * (float(tax_rate) /100)
                        total_tax += tax_amount
                
                    vendor_orders = ordered_products.values('vendor_order').distinct()
                    for vendor_order in vendor_orders:
                        order = RetailVendorOrder.objects.get(id=vendor_order['vendor_order'])
                        discount += order.total_discount_amount
                        vendor_coupon_discount += order.vendor_coupon_discount
                        admin_coupon_discount += order.admin_coupon_discount
                        delivery_charge += order.delivery_charge

        return (total_sales, ordered_products.count(), total_tax, discount, vendor_coupon_discount, admin_coupon_discount, delivery_charge)
    
    def filter_weekly(self, year, month, week, vendor):
        total_sales = 0
        total_tax = 0
        discount = 0
        vendor_coupon_discount = 0
        admin_coupon_discount = 0
        delivery_charge = 0

        if week:

            first_day_of_month = timezone.datetime(year=int(year), month=int(month), day=1).date()

            start_of_week = first_day_of_month + timezone.timedelta(weeks=int(week) - 1)
            start_of_week = start_of_week - timezone.timedelta(days=start_of_week.weekday())  # Adjust to the start of the week (Monday)
            
            end_of_week = start_of_week + timezone.timedelta(days=7)
            
            ordered_products = self.get_ordered_products(vendor).filter(
                created_at__date__gte=start_of_week,
                created_at__date__lt=end_of_week,
                created_at__year=year,
                created_at__month=month
            )
            if ordered_products:
                for product in ordered_products:
                    total_sales += product.price
                    tax_rate = product.tax_rate
                    price = product.price
                    tax_amount = price * (float(tax_rate) /100)
                    total_tax += tax_amount
            
                vendor_orders = ordered_products.values('vendor_order').distinct()
                for vendor_order in vendor_orders:
                    order = RetailVendorOrder.objects.get(id=vendor_order['vendor_order'])
                    discount += order.total_discount_amount
                    vendor_coupon_discount += order.vendor_coupon_discount
                    admin_coupon_discount += order.admin_coupon_discount
                    delivery_charge += order.delivery_charge

        return (total_sales, ordered_products.count(), total_tax,  discount, vendor_coupon_discount, admin_coupon_discount, delivery_charge)