# Generated by Django 5.0 on 2024-04-26 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_vendorinvoices_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='loyalty_points_received',
            field=models.FloatField(default=0.0),
        ),
    ]
