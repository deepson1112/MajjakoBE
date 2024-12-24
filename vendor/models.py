from django.db import models
from user.models import User, UserProfile
from datetime import time, date, datetime
# from user.utils import send_notification
from django.contrib.postgres.fields import ArrayField

class Offerings(models.Model):
    name = models.CharField(max_length = 255)
    description = models.TextField()
    image = models.ImageField(upload_to='vendor/offerings', null=True)

    def __str__(self) -> str:
        return self.name

class Vendor(models.Model):
    user = models.OneToOneField(User, related_name='user', on_delete=models.CASCADE)
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor_slug = models.SlugField(max_length=50, unique=True)
    vendor_license = models.ImageField(upload_to='vendor/license')
    vendor_description = models.TextField(null=True, blank=True)
    vendor_phone = models.CharField(max_length=15, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    tax_rate = models.FloatField(default=0.0)
    tax_exempt = models.BooleanField(default=False)
    age_restriction = models.BooleanField(default=False)
    vendor_cover_image = models.ImageField(upload_to="vendor/vendor_image", null=True, blank=True)
    vendor_logo = models.ImageField(upload_to="vendor/vendor_logo", null=True, blank=True)

    vendor_location = models.CharField(max_length = 255, null=True, blank=True)
    
    vendor_location_latitude = models.CharField(max_length=50, blank=True, null=True)
    vendor_location_longitude = models.CharField(max_length=50, blank=True, null=True)

    VENDOR_TYPE = (
        (1, "Restaurant"),
        (2, "Retails")
    )

    profile_setup = models.BooleanField(default=False)
    vendor_type = models.PositiveSmallIntegerField(
        choices = VENDOR_TYPE, default = 1
    )

    offerings = models.ManyToManyField(Offerings, blank=True)

    def __str__(self):
        return self.vendor_name

    def is_open(self):
        today_date = date.today()
        today = today_date.isoweekday()

        current_opening_hours = OpeningHour.objects.filter(vendor=self, day=today)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        is_open = None
        for i in current_opening_hours:
            if not i.is_closed:
                start = str(datetime.strptime(i.from_hour, "%I:%M %p").time())
                end = str(datetime.strptime(i.to_hour, "%I:%M %p").time())
                if current_time > start and current_time < end:
                    is_open = True
                    break
                else:
                    is_open = False
        return is_open        


    def save(self, *args, **kwarfs):
        if self.pk is not None:
            #update
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                mail_template = 'accounts/emails/admin_approval_email.html'
                context = {
                    'user': self.user,
                    'is_approved': self.is_approved,
                    'to_email': self.user.email,
                }
                if self.is_approved:
                    #send notification email
                    mail_subject='Congratulations! Your restaurant has been approved'
                    # send_notification(mail_subject, mail_template, context)
                else:
                    #send notification email
                    mail_subject = 'Sorry! Your restaurant has been rejected'
                    # send_notification(mail_subject, mail_template, context)

        return super(Vendor, self).save(*args, **kwarfs)


DAYS = [
    (1, ("Monday")),
    (2, ("Tuesday")),
    (3, ("Wednesday")),
    (4, ("Thursday")),
    (5, ("Friday")),
    (6, ("Saturday")),
    (7, ("Sunday")),
]

HOUR_OF_DAY_24 =[(time(h,m).strftime('%I:%M %p'),time(h,m).strftime('%I:%M %p')) for h in range(0,24) for m in (0,30)]


class OpeningHour(models.Model):
    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS)
    from_hour = models.CharField(choices=HOUR_OF_DAY_24,max_length=10,blank=True)
    to_hour = models.CharField(choices=HOUR_OF_DAY_24,max_length=10,blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ('day','-from_hour')
        unique_together =  ('vendor','day','from_hour','to_hour')

    def __str__(self):
        return self.get_day_display()


class VendorHourTimelines(models.Model):
    VENDOR_WEEKDAYS = (
    (0, ("Monday")),
    (1, ("Tuesday")),
    (2, ("Wednesday")),
    (3, ("Thursday")),
    (4, ("Friday")),
    (5, ("Saturday")),
    (6, ("Sunday")),
    )
    starting_hours = models.TimeField()
    ending_hours = models.TimeField()
    hour_name = models.CharField(max_length=255)
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE, null=True)
    week_days = ArrayField(
        models.PositiveSmallIntegerField(choices = VENDOR_WEEKDAYS),
        blank=True,
        null=True,
        default=list
    )

    def __str__(self) -> None:
        return self.hour_name





class FAQS(models.Model):
    question = models.TextField()
    answer = models.TextField()
    order = models.IntegerField()
    active = models.BooleanField(default=True)
    
    def __str__(self) -> str:
        return self.question