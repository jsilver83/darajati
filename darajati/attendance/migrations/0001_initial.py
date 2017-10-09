# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-09 13:05
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('enrollment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pre', 'Present'), ('abs', 'Absent'), ('lat', 'Late'), ('exc', 'Excused')], default='pre', max_length=3, verbose_name='Student attendance')),
                ('updated_on', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'permissions': (('can_give_excused_status', 'Can change student status to excused'),),
            },
        ),
        migrations.CreateModel(
            name='AttendanceInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('comment', models.CharField(blank=True, max_length=150, null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='ScheduledPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('SUNDAY', 'Sunday'), ('MONDAY', 'Monday'), ('TUESDAY', 'Tuesday'), ('WEDNESDAY', 'Wednesday'), ('THURSDAY', 'Thursday'), ('FRIDAY', 'Friday'), ('SATURDAY', 'Saturday')], max_length=9, null=True)),
                ('title', models.CharField(max_length=20, null=True)),
                ('start_time', models.TimeField(verbose_name='start time')),
                ('end_time', models.TimeField(verbose_name='end time')),
                ('location', models.CharField(max_length=50, null=True)),
                ('late_deduction', models.DecimalField(decimal_places=2, max_digits=5, null=True, verbose_name='late deduction')),
                ('absence_deduction', models.DecimalField(decimal_places=2, max_digits=5, null=True, verbose_name='absence deduction')),
                ('instructor_assigned', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_periods', to='enrollment.Instructor')),
                ('section', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_periods', to='enrollment.Section')),
            ],
        ),
        migrations.AddField(
            model_name='attendanceinstance',
            name='period',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_dates', to='attendance.ScheduledPeriod'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='attendance_instance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='attendance.AttendanceInstance'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='enrollment.Enrollment'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
