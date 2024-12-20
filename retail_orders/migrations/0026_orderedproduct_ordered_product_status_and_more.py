# Generated by Django 4.2.16 on 2024-11-24 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail_orders', '0025_retailorder_nation'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderedproduct',
            name='ordered_product_status',
            field=models.CharField(blank=True, choices=[('New', 'New'), ('Accepted', 'Accepted'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='New', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='retailorder',
            name='status',
            field=models.CharField(choices=[('New', 'New'), ('Completed', 'Completed')], default='New', max_length=15),
        ),
    ]
