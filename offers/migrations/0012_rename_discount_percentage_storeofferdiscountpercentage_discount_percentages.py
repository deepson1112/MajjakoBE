# Generated by Django 5.0 on 2024-03-04 05:03

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("offers", "0011_freedelivery_discount_banner_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="storeofferdiscountpercentage",
            old_name="discount_percentage",
            new_name="discount_percentages",
        ),
    ]
