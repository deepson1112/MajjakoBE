# Generated by Django 5.1.4 on 2024-12-23 06:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('menu', '0002_initial'),
        ('offers', '0001_initial'),
        ('vendor', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='coupons',
            name='vendor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='coupons', to='vendor.vendor'),
        ),
        migrations.AddField(
            model_name='freedelivery',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='getonefreeoffer',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='getonefreeoffer',
            name='item',
            field=models.ManyToManyField(to='menu.fooditem'),
        ),
        migrations.AddField(
            model_name='getonefreeoffer',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vendor.vendor'),
        ),
        migrations.AddField(
            model_name='saveonitemsdiscountpercentage',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='save_on_item', to='menu.vendorcategories'),
        ),
        migrations.AddField(
            model_name='saveonitemsdiscountpercentage',
            name='item',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='save_on_item', to='menu.fooditem'),
        ),
        migrations.AddField(
            model_name='saveonitemsoffer',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='saveonitemsoffer',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vendor.vendor'),
        ),
        migrations.AddField(
            model_name='saveonitemsdiscountpercentage',
            name='store_offer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offer_items', to='offers.saveonitemsoffer'),
        ),
        migrations.AddField(
            model_name='storeoffer',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='storeoffer',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vendor.vendor'),
        ),
    ]
