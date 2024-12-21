from django.contrib import admin
from user.models import User, UserProfile, UserLocation, Notification
from allauth.socialaccount.models  import SocialAccount

# Register your models here.
admin.site.register(User)
# admin.site.register(SocialAccount)

admin.site.register(UserProfile)
admin.site.register(UserLocation)
admin.site.register(Notification)


