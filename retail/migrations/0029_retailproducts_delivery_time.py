# Generated by Django 4.2.16 on 2024-11-21 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0028_searchkeyword_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailproducts',
            name='delivery_time',
            field=models.CharField(blank=True, choices=[('same day delivery', 'same day delivery'), ('1-2 days', '1-2 days'), ('3-5 days', '3-5 days'), ('5-7 days', '5-7 days')], default='same day delivery', max_length=50, null=True),
        ),
    ]
