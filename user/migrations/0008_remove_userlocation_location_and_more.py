# Generated by Django 5.0 on 2024-08-05 03:24

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0007_user_guest_user"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userlocation",
            name="location",
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="location",
        ),
    ]
