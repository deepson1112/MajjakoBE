# Generated by Django 4.2.7 on 2024-10-07 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail_offers', '0025_retailfreedelivery'),
    ]

    operations = [
        migrations.AlterField(
            model_name='retailfreedelivery',
            name='discount_banner',
            field=models.ImageField(blank=True, null=True, upload_to='free_delivery/'),
        ),
    ]
