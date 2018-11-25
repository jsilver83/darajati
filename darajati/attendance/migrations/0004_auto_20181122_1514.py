# Generated by Django 2.0.1 on 2018-11-22 12:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0008_auto_20180702_1516'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0003_excuse'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalAttendance',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('status', models.CharField(choices=[('pre', 'Present'), ('abs', 'Absent'), ('lat', 'Late'), ('exc', 'Excused')], default='pre', max_length=3, verbose_name='Student attendance')),
                ('updated_on', models.DateTimeField(blank=True, editable=False, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('attendance_instance', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='attendance.AttendanceInstance')),
                ('enrollment', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='enrollment.Enrollment')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical attendance',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('attendance_instance', 'enrollment')},
        ),
    ]