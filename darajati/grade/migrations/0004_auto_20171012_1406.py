# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-12 11:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0003_gradefragment_student_total_grading'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgrade',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='enrollment.UserProfile'),
        ),
    ]
