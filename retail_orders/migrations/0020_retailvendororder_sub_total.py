# Generated by Django 4.2.7 on 2024-10-02 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail_orders', '0019_retailvendororder_loyalty_discount_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailvendororder',
            name='sub_total',
            field=models.FloatField(default=0.0),
        ),
    ]
