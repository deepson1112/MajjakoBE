# Generated by Django 4.2.7 on 2024-06-06 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0007_alter_vendorhourtimelines_week_days"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="vendor_description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vendor",
            name="vendor_phone",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
