# Generated by Django 5.0 on 2024-04-27 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_ordercustomization_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ordercustomization',
            name='receiver_name',
        ),
        migrations.AddField(
            model_name='orderedfood',
            name='receiver_name',
            field=models.CharField(default=''),
        ),
    ]
