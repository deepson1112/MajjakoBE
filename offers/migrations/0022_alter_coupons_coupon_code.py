# Generated by Django 5.0 on 2024-03-27 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0021_storeoffer_discount_percentages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupons',
            name='coupon_code',
            field=models.CharField(help_text='max length = 25', max_length=25, unique=True),
        ),
    ]
