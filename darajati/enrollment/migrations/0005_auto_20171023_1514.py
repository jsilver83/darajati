# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-23 12:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0004_auto_20171023_1135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coordinator',
            name='instructor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='coordinators', to='enrollment.Instructor'),
        ),
    ]