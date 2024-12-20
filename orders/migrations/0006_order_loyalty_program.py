# Generated by Django 5.0 on 2024-04-23 07:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0026_loyaltyprograms_minimum_spend_amount_and_more'),
        ('orders', '0005_paymentinfo_payment_alter_payment_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='loyalty_program',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='loyalty_orders', to='offers.loyaltyprograms'),
        ),
    ]
