# Generated by Django 5.0 on 2024-06-01 06:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0024_alter_vendorcategories_department'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='foodaddonsfoodjunction',
            unique_together=set(),
        ),
    ]
