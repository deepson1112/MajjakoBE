# Generated by Django 4.2.16 on 2024-12-20 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail_orders', '0032_remove_orderedproductstatus_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='retailorder',
            name='pin_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
