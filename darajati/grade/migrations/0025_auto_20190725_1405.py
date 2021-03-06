# Generated by Django 2.2.3 on 2019-07-25 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0012_courseoffering_letter_grade_promotion_borderline'),
        ('grade', '0024_auto_20190115_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradefragment',
            name='letter_grade_promotion_criterion',
            field=models.BooleanField(default=0, help_text='This if checked indicates the criterion for which coordinators can promote final letter grades for students who performed in it better than their letter grade. There should be only one fragment for the whole course offering that can be flagged as the criterion.', verbose_name='Letter Grade Promotion Criterion?'),
        ),
        migrations.AlterField(
            model_name='gradefragment',
            name='entry_in_percentages',
            field=models.BooleanField(blank=True, default=False, help_text='Checked when the course entered grades are in %', verbose_name='Entry in Percentages'),
        ),
        migrations.AlterUniqueTogether(
            name='lettergrade',
            unique_together={('course_offering', 'letter_grade'), ('section', 'letter_grade')},
        ),
    ]
