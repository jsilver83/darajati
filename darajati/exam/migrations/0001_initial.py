# Generated by Django 2.0.1 on 2018-11-07 11:15

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('enrollment', '0008_auto_20180702_1516'),
        ('grade', '0009_historicalstudentgrade'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capacity', models.PositiveIntegerField(null=True, verbose_name='Room Capacity')),
            ],
            options={
                'ordering': ['exam_shift', 'room'],
            },
        ),
        migrations.CreateModel(
            name='ExamShift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(null=True, verbose_name='Shift Start Date')),
                ('end_date', models.DateTimeField(null=True, verbose_name='Shift End Date')),
                ('fragment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exams_shifts', to='grade.GradeFragment', verbose_name='Fragment')),
            ],
            options={
                'ordering': ['fragment', 'start_date'],
            },
        ),
        migrations.CreateModel(
            name='Marker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(help_text='This is the order in which after marker 1 finish the markings for marker 2 will start..', null=True, verbose_name='Marking Order')),
                ('generosity_factor', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Generosity factor for this instructor, can be in minus. Make sure it is in percent', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(Decimal('-100.00')), django.core.validators.MaxValueValidator(Decimal('100.00'))], verbose_name='Generosity Factor')),
                ('is_a_monitor', models.BooleanField(default=False, verbose_name='Is a Monitor?')),
                ('updated_on', models.DateTimeField(auto_now=True, verbose_name='Updated On')),
                ('exam_room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='markers', to='exam.ExamRoom', verbose_name='Instructor')),
                ('instructor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marking', to='enrollment.Instructor', verbose_name='Instructor')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'ordering': ['exam_room', 'order', 'instructor'],
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True, verbose_name='Room Name')),
                ('location', models.CharField(max_length=100, null=True, verbose_name='Room location')),
                ('capacity', models.PositiveIntegerField(default=0, verbose_name='Room Capacity')),
                ('updated_on', models.DateTimeField(auto_now=True, verbose_name='Updated On')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['location'],
            },
        ),
        migrations.CreateModel(
            name='StudentMark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mark', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), django.core.validators.MaxValueValidator(Decimal('100.00'))], verbose_name='Student Grade Quantity')),
                ('updated_on', models.DateTimeField(auto_now=True, verbose_name='Updated On')),
                ('marker', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='markings', to='exam.Marker')),
            ],
            options={
                'ordering': ['student_placement', 'marker'],
            },
        ),
        migrations.CreateModel(
            name='StudentPlacement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_present', models.BooleanField(default=True, verbose_name='Is Present?')),
                ('shuffled_on', models.DateTimeField(auto_now=True, verbose_name='Shuffled On')),
                ('enrollment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='enrollment.Enrollment')),
                ('exam_room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='students', to='exam.ExamRoom', verbose_name='Exam Room')),
                ('shuffled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Shuffled By')),
            ],
            options={
                'ordering': ['enrollment'],
            },
        ),
        migrations.AddField(
            model_name='studentmark',
            name='student_placement',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='marks', to='exam.StudentPlacement', verbose_name='Student Placement'),
        ),
        migrations.AddField(
            model_name='studentmark',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='examroom',
            name='exam_shift',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='exam.ExamShift', verbose_name='Exam Shift'),
        ),
        migrations.AddField(
            model_name='examroom',
            name='room',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='exam.Room', verbose_name='Exam Room'),
        ),
    ]
