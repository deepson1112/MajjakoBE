from django.db import models

# Create your models here.
class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    newsletter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self) -> str:
        return self.first_name