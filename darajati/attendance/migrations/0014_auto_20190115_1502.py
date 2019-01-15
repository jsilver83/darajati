# Generated by Django 2.0.1 on 2019-01-15 12:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0013_attendancedeductionview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledperiod',
            name='instructor_assigned',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_periods', to='enrollment.Instructor'),
        ),
    ]
