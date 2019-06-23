# Generated by Django 2.0.1 on 2019-01-15 12:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0009_auto_20181227_1320'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coordinator',
            options={'ordering': ('course_offering', 'instructor')},
        ),
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ('department', 'code', 'name')},
        ),
        migrations.AlterModelOptions(
            name='courseoffering',
            options={'ordering': ('semester', 'course')},
        ),
        migrations.AlterModelOptions(
            name='department',
            options={'ordering': ('code', 'name')},
        ),
        migrations.AlterModelOptions(
            name='instructor',
            options={'ordering': ('-user__is_superuser', '-user__is_staff', 'english_name', 'university_id')},
        ),
        migrations.AlterModelOptions(
            name='section',
            options={'ordering': ('course_offering', 'code')},
        ),
        migrations.AlterModelOptions(
            name='semester',
            options={'ordering': ('-start_date', 'code')},
        ),
        migrations.AlterModelOptions(
            name='student',
            options={'ordering': ('university_id',)},
        ),
        migrations.AlterField(
            model_name='course',
            name='department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='enrollment.Department'),
        ),
        migrations.AlterField(
            model_name='enrollment',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_enrollments', to=settings.AUTH_USER_MODEL),
        ),
    ]