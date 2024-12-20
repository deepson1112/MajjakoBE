# Generated by Django 5.0 on 2024-07-24 14:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0008_retailproductsvariations_specifications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productsvariationsimage',
            name='variation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variations_image', to='retail.retailproductsvariations'),
        ),
    ]
