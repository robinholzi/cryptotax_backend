# Generated by Django 3.1.7 on 2022-01-04 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_analysis', '0025_currencypricecache'),
    ]

    operations = [
        migrations.AddField(
            model_name='currencypricecache',
            name='price',
            field=models.FloatField(default=1, verbose_name='price'),
            preserve_default=False,
        ),
    ]
