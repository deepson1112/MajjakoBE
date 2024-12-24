# Generated by Django 5.1.4 on 2024-12-23 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('maximum_number', models.IntegerField(default=0)),
                ('description', models.CharField(help_text='This is the description for the addons, max_length = 255', max_length=225, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='addons/')),
                ('multiple_selection', models.BooleanField(default=False)),
                ('secondary_customization', models.BooleanField(default=False)),
                ('customization_order', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='CustomizationTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minimum_quantity', models.PositiveSmallIntegerField()),
                ('maximum_quantity', models.FloatField()),
                ('description', models.TextField(null=True)),
                ('add_on_category', models.CharField(max_length=255)),
                ('select_type', models.CharField(choices=[('SINGLE', 'SINGLE'), ('MULTIPLE', 'MULTIPLE')], default='SINGLE', max_length=225)),
            ],
        ),
        migrations.CreateModel(
            name='FoodAddonsFoodJunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_addons_order', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='FoodItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_title', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, max_length=250)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('image', models.ImageField(null=True, upload_to='foodimages')),
                ('is_available', models.BooleanField(default=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('food_item_order', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='VendorCategories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_name', models.CharField(max_length=255)),
                ('category_slug', models.SlugField()),
                ('category_description', models.TextField(null=True)),
                ('tax_rate', models.FloatField(default=0.0)),
                ('tax_exempt', models.BooleanField(default=False)),
                ('age_restriction', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('categories_order', models.IntegerField(default=0)),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='department/')),
                ('vendor_type', models.PositiveSmallIntegerField(choices=[(1, 'Restaurant'), (2, 'Retails')], default=2, null=True)),
            ],
            options={
                'ordering': ['categories_order'],
            },
        ),
        migrations.CreateModel(
            name='VendorDepartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department_name', models.CharField(help_text='Department name', max_length=255)),
                ('department_slug', models.SlugField()),
                ('tax_rate', models.FloatField(default=0.0)),
                ('tax_exempt', models.BooleanField(default=False)),
                ('age_restriction', models.BooleanField(default=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='department/')),
                ('vendor_type', models.PositiveSmallIntegerField(choices=[(1, 'Restaurant'), (2, 'Retails')], default=2, null=True)),
                ('department_order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['department_order'],
            },
        ),
    ]
