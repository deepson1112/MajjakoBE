# Generated by Django 5.0 on 2024-06-23 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0013_remove_vendor_is_restaurant_remove_vendor_is_retail_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FAQS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('order', models.IntegerField()),
                ('active', models.BooleanField(default=True)),
            ],
        ),
    ]
