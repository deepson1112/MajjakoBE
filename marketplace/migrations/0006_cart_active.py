# Generated by Django 5.0 on 2024-03-05 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0005_cart_receiver_name_alter_cart_fooditem_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
