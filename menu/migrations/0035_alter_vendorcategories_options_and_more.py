# Generated by Django 4.2.7 on 2024-09-30 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0034_alter_vendorcategories_vendor_type_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vendorcategories',
            options={'ordering': ['categories_order']},
        ),
        migrations.AlterField(
            model_name='vendorcategories',
            name='categories_order',
            field=models.IntegerField(default=0),
        ),
    ]
