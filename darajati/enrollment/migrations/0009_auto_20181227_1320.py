# Generated by Django 2.0.1 on 2018-12-27 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0008_auto_20180702_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoffering',
            name='total_decimal_places',
            field=models.SmallIntegerField(blank=True, help_text='Decimal places in the Total for rounding or truncating methods', null=True, verbose_name='Total Rounding Decimal Places'),
        ),
        migrations.AddField(
            model_name='section',
            name='total_decimal_places',
            field=models.SmallIntegerField(blank=True, help_text='Decimal places in the Total for rounding or truncating methods', null=True, verbose_name='Total Rounding Decimal Places'),
        ),
        migrations.AlterField(
            model_name='courseoffering',
            name='total_rounding_type',
            field=models.CharField(choices=[('ceil', 'Ceiling'), ('floor', 'Floor'), ('round', 'Round'), ('trunc', 'Truncate'), ('none', 'None')], default='none', help_text='Total grade rounding method for letter grade calculation', max_length=50, null=True, verbose_name='Total Rounding Type'),
        ),
        migrations.AlterField(
            model_name='section',
            name='rounding_type',
            field=models.CharField(choices=[('ceil', 'Ceiling'), ('floor', 'Floor'), ('round', 'Round'), ('trunc', 'Truncate'), ('none', 'None')], default='none', help_text='Total grade rounding method for letter grade calculation', max_length=50, null=True, verbose_name='Rounding Type'),
        ),
    ]
