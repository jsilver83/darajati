# Generated by Django 2.0.1 on 2018-11-15 04:44

import attendance.media_handlers
import darajati.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0002_auto_20171112_1354'),
    ]

    operations = [
        migrations.CreateModel(
            name='Excuse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(null=True, verbose_name='Start Date/Time')),
                ('end_date', models.DateTimeField(null=True, verbose_name='End Date/Time')),
                ('university_id', models.CharField(max_length=20, null=True, verbose_name='University ID')),
                ('excuse_type', models.CharField(choices=[('clinics_medical', 'Medical (KFUPM Clinics)'), ('outside_medical', 'Medical (Outside)'), ('personal', 'Personal Excuse'), ('other', 'Other')], default='clinics_medical', max_length=30, null=True, verbose_name='Excuse')),
                ('includes_exams', models.BooleanField(default=False, verbose_name='Includes Exams?')),
                ('attachments', models.FileField(blank=True, null=True, upload_to=attendance.media_handlers.upload_excuse_attachments, validators=[darajati.validators.validate_file_extension], verbose_name='Attachments')),
                ('description', models.CharField(blank=True, max_length=2000, null=True, verbose_name='Description')),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created On')),
                ('applied_on', models.DateTimeField(blank=True, null=True, verbose_name='Applied On')),
                ('applied_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applied_excuses', to=settings.AUTH_USER_MODEL, verbose_name='Applied By')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_excuses', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
            ],
            options={
                'permissions': (('can_give_excuses', 'Can enter excuses for students'),),
            },
        ),
    ]