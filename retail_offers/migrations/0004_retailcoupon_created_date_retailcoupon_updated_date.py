# Generated by Django 4.2.7 on 2024-08-08 06:32

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('retail_offers', '0003_retailcoupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailcoupon',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='retailcoupon',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
