# Generated by Django 2.0.1 on 2018-11-22 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0009_historicalstudentgrade'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gradefragment',
            name='allow_subjective_marking',
        ),
        migrations.AlterField(
            model_name='gradefragment',
            name='boundary_type',
            field=models.CharField(choices=[('OBJECTIVE', 'Objective'), ('SUBJECTIVE_BOUNDED', 'Subjective bound'), ('SUBJECTIVE_BOUNDED_FIXED', 'Subjective bound Fixed'), ('SUBJECTIVE_FREE', 'Subjective Free'), ('SUBJECTIVE_MARKING', 'Subjective Marking')], default='SUBJECTIVE_FREE', max_length=24, null=True, verbose_name='Boundary Type'),
        ),
    ]
