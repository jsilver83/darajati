# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-07 10:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0003_auto_20171023_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradefragment',
            name='entry_end_date',
            field=models.DateTimeField(help_text='Set the entry date and time to allow instructor to enter grades', null=True, verbose_name='Allowed entry start date'),
        ),
        migrations.AddField(
            model_name='gradefragment',
            name='entry_start_date',
            field=models.DateTimeField(help_text='Set the entry date and time to allow instructor to enter grades', null=True, verbose_name='Allowed entry start date'),
        ),
    ]
