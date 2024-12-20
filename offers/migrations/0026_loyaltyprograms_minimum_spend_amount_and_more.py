# Generated by Django 5.0 on 2024-04-23 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0025_loyaltysettings_remove_coupons_created_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='loyaltyprograms',
            name='minimum_spend_amount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='loyaltyprograms',
            name='program_code',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
    ]
