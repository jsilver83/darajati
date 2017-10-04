# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-05 07:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('enrollment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradeFragment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(help_text='Categories are like: Quiz, Midterm, Final Exam etc..', max_length=100, null=True, verbose_name='Category')),
                ('description', models.CharField(max_length=100, null=True, verbose_name='Description')),
                ('weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=4, null=True, verbose_name='Weight')),
                ('allow_entry', models.BooleanField(default=True, help_text='Allowing instructor to enter the marks for this grade break down', verbose_name='Allow Entry')),
                ('order', models.PositiveSmallIntegerField(help_text='The order of which grade break down should show up first', null=True, verbose_name='Display Order')),
                ('show_teacher_report', models.BooleanField(default=True, verbose_name='Show in Teacher Report')),
                ('show_student_report', models.BooleanField(default=True, verbose_name='Show in Student Report')),
                ('boundary_type', models.CharField(choices=[('OBJECTIVE', 'Objective'), ('SUBJECTIVE_BOUNDED', 'Subjective Bounded'), ('SUBJECTIVE_BOUNDED_FIXED', 'Subjective Bounded Fixed'), ('SUBJECTIVE_FREE', 'Subjective Free')], default='SUBJECTIVE_FREE', max_length=20, null=True, verbose_name='Boundary Type')),
                ('boundary_range', models.DecimalField(blank=True, decimal_places=2, help_text='When the type is subjective and it is not free, give a range +-', max_digits=4, null=True, verbose_name='Boundary Range')),
                ('boundary_fixed_average', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name='Boundary Fixed Average')),
                ('allow_change', models.BooleanField(default=True, verbose_name='Allow Change After Submission')),
                ('allow_subjective_marking', models.BooleanField(default=False, verbose_name='Allow Subjective Marking')),
                ('entry_in_percentages', models.BooleanField(default=False, help_text='Checked when the course entered grades are in %', verbose_name='Entry in Percentages')),
                ('updated_on', models.DateField(auto_now=True, verbose_name='Updated On')),
                ('course_offering', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='GradeFragment', to='enrollment.CourseOffering')),
                ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='GradeFragment', to='enrollment.Section')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='GradeFragment', to='enrollment.UserProfile')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='LetterGrade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter_grade', models.CharField(max_length=5, null=True, verbose_name='Letter Grade')),
                ('cut_off_point', models.DecimalField(decimal_places=2, default=0.0, max_digits=4, null=True, verbose_name='Cut off Point')),
                ('updated_on', models.DateField(auto_now=True, verbose_name='Updated On')),
                ('course_offering', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='letter_grades', to='enrollment.CourseOffering')),
                ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='letter_grades', to='enrollment.Section')),
                ('updated_by', models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='letter_grade', to='enrollment.UserProfile')),
            ],
        ),
        migrations.CreateModel(
            name='StudentGrade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade_quantity', models.DecimalField(decimal_places=2, max_digits=4, null=True, verbose_name='Student Grade Quantity')),
                ('remarks', models.CharField(blank=True, max_length=100, null=True, verbose_name='Instructor Remarks')),
                ('updated_on', models.DateField(auto_now=True, verbose_name='Updated On')),
                ('enrollment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='enrollment.Enrollment')),
                ('grade_fragment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='grade.GradeFragment')),
                ('updated_by', models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='enrollment.UserProfile')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='studentgrade',
            unique_together=set([('enrollment', 'grade_fragment')]),
        ),
    ]