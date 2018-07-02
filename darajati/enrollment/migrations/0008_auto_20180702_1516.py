# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-02 12:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0007_courseoffering_formula'),
    ]

    operations = [
        migrations.AlterField(
            model_name='semester',
            name='end_date',
            field=models.DateField(verbose_name='End date'),
        ),
        migrations.AlterField(
            model_name='semester',
            name='grade_fragment_deadline',
            field=models.DateField(null=True, verbose_name='Grade break down deadline date'),
        ),
        migrations.AlterField(
            model_name='semester',
            name='start_date',
            field=models.DateField(verbose_name='Start date'),
        ),
    ]
