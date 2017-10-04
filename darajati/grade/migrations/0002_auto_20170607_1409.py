# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-07 11:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradefragment',
            name='boundary_fixed_average',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Boundary Fixed Average'),
        ),
        migrations.AlterField(
            model_name='gradefragment',
            name='boundary_range',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='When the type is subjective and it is not free, give a range +-', max_digits=5, null=True, verbose_name='Boundary Range'),
        ),
        migrations.AlterField(
            model_name='gradefragment',
            name='weight',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, null=True, verbose_name='Weight'),
        ),
        migrations.AlterField(
            model_name='lettergrade',
            name='cut_off_point',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, null=True, verbose_name='Cut off Point'),
        ),
        migrations.AlterField(
            model_name='studentgrade',
            name='grade_quantity',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True, verbose_name='Student Grade Quantity'),
        ),
    ]