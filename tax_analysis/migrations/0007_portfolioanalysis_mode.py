# Generated by Django 3.2.10 on 2021-12-20 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_analysis', '0006_auto_20211220_2327'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolioanalysis',
            name='mode',
            field=models.CharField(choices=[('P', 'PROCESSING'), ('A', 'ANALYSING'), ('F', 'FINISHED')], default='P', max_length=2),
            preserve_default=False,
        ),
    ]