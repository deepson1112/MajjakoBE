# Generated by Django 4.2.16 on 2024-12-17 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_contact_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='seen',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
