# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-17 12:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='AttendanceInstant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('comment', models.CharField(blank=True, max_length=150, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, null=True)),
                ('code', models.CharField(max_length=20, null=True)),
                ('description', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, null=True)),
                ('arabic_name', models.CharField(max_length=50, null=True)),
                ('code', models.CharField(max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Enrolment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter_grade', models.CharField(default='UD', max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university_id', models.CharField(blank=True, max_length=20, null=True)),
                ('government_id', models.CharField(blank=True, max_length=20, null=True)),
                ('english_name', models.CharField(max_length=255, null=True)),
                ('arabic_name', models.CharField(max_length=255, null=True)),
                ('mobile', models.CharField(blank=True, max_length=20, null=True)),
                ('personal_email', models.EmailField(max_length=254, null=True)),
                ('active', models.BooleanField(default=False)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='instructor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScheduledPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('sun', 'Sunday'), ('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday')], max_length=3, null=True)),
                ('title', models.CharField(max_length=20, null=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('location', models.CharField(max_length=50, null=True)),
                ('late_deduction', models.FloatField(default=0.0, null=True)),
                ('absence_deduction', models.FloatField(default=0.0, null=True)),
                ('instructor_assigned', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_periods', to='attendances_and_grades.Instructor')),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='attendances_and_grades.Course')),
            ],
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('code', models.CharField(max_length=20, null=True)),
                ('description', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university_id', models.CharField(blank=True, max_length=20, null=True)),
                ('government_id', models.CharField(blank=True, max_length=20, null=True)),
                ('english_name', models.CharField(max_length=255, null=True)),
                ('arabic_name', models.CharField(max_length=255, null=True)),
                ('mobile', models.CharField(blank=True, max_length=20, null=True)),
                ('personal_email', models.EmailField(max_length=254, null=True)),
                ('active', models.BooleanField(default=False)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='section',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='attendances_and_grades.Semester'),
        ),
        migrations.AddField(
            model_name='scheduledperiod',
            name='section',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_periods', to='attendances_and_grades.Section'),
        ),
        migrations.AddField(
            model_name='enrolment',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolments', to='attendances_and_grades.Section'),
        ),
        migrations.AddField(
            model_name='enrolment',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolments', to='attendances_and_grades.Student'),
        ),
        migrations.AddField(
            model_name='course',
            name='department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='attendances_and_grades.Department'),
        ),
        migrations.AddField(
            model_name='attendanceinstant',
            name='period',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_dates', to='attendances_and_grades.ScheduledPeriod'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='attendance_instant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='attendances_and_grades.AttendanceInstant'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='enrolment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='attendances_and_grades.Enrolment'),
        ),
    ]
