# Generated by Django 4.2.7 on 2024-09-01 08:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('retail', '0013_remove_productsvariationsimage_variation_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RetailRefundItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('reason', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('in_review', 'In Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='in_review', max_length=50)),
                ('image_1', models.ImageField(upload_to='refund-products/')),
                ('image_2', models.ImageField(blank=True, null=True, upload_to='refund-products/')),
                ('image_3', models.ImageField(blank=True, null=True, upload_to='refund-products/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_refund', to='retail.retailproducts')),
            ],
        ),
        migrations.CreateModel(
            name='RetailRefund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('refund_products', models.ManyToManyField(related_name='refunds', to='retail_refund.retailrefunditem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
