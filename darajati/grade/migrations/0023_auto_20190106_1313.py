# Generated by Django 2.0.1 on 2019-01-06 10:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0022_studentfinaldataview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradefragment',
            name='course_offering',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grade_fragments', to='enrollment.CourseOffering'),
        ),
    ]
