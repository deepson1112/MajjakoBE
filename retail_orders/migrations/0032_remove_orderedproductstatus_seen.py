# Generated by Django 4.2.16 on 2024-12-02 06:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('retail_orders', '0031_orderedproductstatus_seen'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderedproductstatus',
            name='seen',
        ),
    ]
