# Generated by Django 3.1.7 on 2021-12-27 08:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0011_auto_20211225_1003'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='buy_datetime',
            field=models.DateTimeField(default=datetime.datetime(2021, 12, 27, 9, 50, 27, 581756), verbose_name='buy_datetime'),
            preserve_default=False,
        ),
    ]
