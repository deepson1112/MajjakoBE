# Generated by Django 5.1.4 on 2024-12-23 06:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('marketplace', '0002_initial'),
        ('menu', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='foodcustomizations',
            name='cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cart_addons', to='marketplace.cart'),
        ),
        migrations.AddField(
            model_name='foodcustomizations',
            name='customization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cart_menu', to='menu.customization'),
        ),
    ]
