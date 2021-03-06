# Generated by Django 2.0.1 on 2019-01-08 14:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0009_auto_20181227_1320'),
        ('attendance', '0012_removed_rowno_attendancededuction'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceDeductionView',
            fields=[
                ('enrollment', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='attendance_deduction', serialize=False, to='enrollment.Enrollment')),
                ('attendance_deduction', models.DecimalField(decimal_places=4, max_digits=10)),
            ],
            options={
                'managed': False,
                'db_table': 'enrollment_attendancededuction',
            },
        ),
    ]
