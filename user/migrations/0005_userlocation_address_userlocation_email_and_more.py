# Generated by Django 5.0 on 2024-04-15 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_userlocation'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlocation',
            name='address',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='userlocation',
            name='email',
            field=models.EmailField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userlocation',
            name='first_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userlocation',
            name='last_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userlocation',
            name='phone_number',
            field=models.CharField(blank=True, max_length=12),
        ),
    ]
