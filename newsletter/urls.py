from rest_framework.routers import DefaultRouter

from newsletter.views import NewsletterViewSet, AdminNewsletterViewSet
from django.urls import path

router =DefaultRouter()

router.register('subscribe', NewsletterViewSet, basename='subscribe')

custom_urlpatterns = [
    path('subscribe', NewsletterViewSet.as_view({'post': 'create'}), name='newsletter-subscribe-no-slash'),
    path('admin-newsletter', AdminNewsletterViewSet.as_view({'get': 'list'}), name='newsletter-list'),
]

urlpatterns = custom_urlpatterns + router.urls