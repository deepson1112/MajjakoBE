# Generated by Django 4.2.7 on 2024-09-25 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail_offers', '0021_alter_vendorplatformoffer_retail_product_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailgetonefreeoffer',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='retailsaveonitemsoffer',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='retailstoreoffer',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]
