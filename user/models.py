from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, AbstractUser
# Create your models here.
# from django.contrib.gis.db import models as gismodels
# from django.contrib.gis.geos import Point


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, role=2, password="None",guest_user=False, active=False):
        if not email:
            raise ValueError("User must have an email address")

        if not username:
            raise ValueError("User must have an username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            guest_user=guest_user,
            is_active=active,
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, first_name, last_name, username, email, role=2, password=None):

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=True,
            is_active=True,
            is_superuser=True,
        )
        user.set_password(password)
        user.save()
        return user


class User(AbstractUser):
    ROLE_CHOICE = (
        (1, 'Vendor'),
        (2, 'Customer'),
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    role = models.PositiveSmallIntegerField(
        choices=ROLE_CHOICE, null=True, blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    first_login = models.BooleanField(default=False)
    guest_user = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    def has_module_perms(self, perm, obj=None):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def get_role(self, role, obj=None):
        return "Vendor" if role == 1 else "Customer"

NATION = (
        ('NP', 'NP'),
        ('US', 'US'),
    )

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name = 'user_profile')
    profile_picture = models.ImageField(
        upload_to='users/profile_pictures', blank=True, null=True)
    cover_photo = models.ImageField(
        upload_to='users/cover_photos', blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)

    country = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    pin_code = models.CharField(max_length=6, blank=True, null=True)
    latitude = models.CharField(max_length=50, blank=True, null=True)
    longitude = models.CharField(max_length=50, blank=True, null=True)
    # location = gismodels.PointField(srid=4326, blank=True, null=True)
    applied_coupon = models.TextField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    loyalty_points = models.FloatField(default=0.0)
    
    profile_setup = models.BooleanField(default=False, null=True, blank=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_mobile_verified = models.BooleanField(default=False)
    mobile_otp = models.CharField(max_length=32, null=True, blank=True)

    nation = models.CharField(max_length=5, choices=NATION, null=True, blank=True)


    # def full_address(self):s
    #     return f"{self.address_line_1}, {self.address_line_2}"

    def __str__(self):
        try:
            return self.user.email
        except:
            return str(self.id)
        
    # def save(self, *args, **kwargs):
    #     if self.latitude and self.longitude:
    #         self.location = Point(float(self.longitude), float(self.latitude))
    #         return super(UserProfile, self).save(*args, **kwargs)
    #     return super(UserProfile, self).save(*args, **kwargs)


class UserLocation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name = 'user_location')
    address =  models.CharField(max_length=250, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    pin_code = models.CharField(max_length=6, blank=True, null=True)
    latitude = models.CharField(max_length=50, blank=True, null=True)
    longitude = models.CharField(max_length=50, blank=True, null=True)

    # location = gismodels.PointField(srid=4326, blank=True, null=True)

    first_name = models.CharField(max_length=50,blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True, null=True )

    is_mobile_verified = models.BooleanField(default=False)
    mobile_otp = models.CharField(max_length=32, null=True, blank=True)

    nation = models.CharField(max_length=5, choices=NATION, null=True, blank=True)

    def __str__(self) -> str:
        return self.user.first_name

class Notification(models.Model):
    user = models.ManyToManyField(User, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(null=True, blank=True)
    image = models.ImageField(upload_to='notification_image', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    seen = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self) -> str:
        return self.title