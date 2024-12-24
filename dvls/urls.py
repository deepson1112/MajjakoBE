"""
URL configuration for dvls project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# from django.forms import ValidationError
from rest_framework.exceptions import ValidationError
from django.urls import path, include
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from debug_toolbar.toolbar import debug_toolbar_urls

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)

def redirect_to_token_obtain_pair(request):
    if request.method == 'POST':
        return redirect('/user/token/')
    return JsonResponse({"error": "GET method not allowed for login. Use POST."}, status=405)



urlpatterns = [
    path('docs/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    # path("api-auth/", include("rest_framework.urls")),

    path('api-auth/login/', redirect_to_token_obtain_pair, name='redirect_to_token_obtain'),
    path('auth/', include('djoser.urls.jwt')),
    path('user/', include('user.urls')),
    path('vendor/', include('vendor.urls')),
    path('menu/', include('menu.urls')),
    path('marketplace/', include('marketplace.urls')),
    path('offers/', include('offers.urls')),
    path('orders/', include('orders.urls')),

    path('retails/', include('retail.urls')),
    path('retail-marketplace/', include('retail_marketplace.urls')),
    path('retail-offers/', include('retail_offers.urls')),
    path('retail-orders/', include('retail_orders.urls')),
    path('retail-wishlist/', include('retail_wishlist.urls')),
    path('retail-refund/', include('retail_refund.urls')),
    path('retail-product-display/', include('retail_product_display.urls')),
    path('retail-logistics/', include('retail_logistics.urls')),
    path('homepage/', include('homepage.urls')),
    path('watchlist/', include('watchlist.urls')),
    path('newsletter/', include('newsletter.urls')),
    path('contact/', include('contact.urls')),
    path('review/', include('retail_review.urls')),

    path('accounts/', include('allauth.urls')),




] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + debug_toolbar_urls()
