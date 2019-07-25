# Generated by Django 2.2.3 on 2019-07-25 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0011_auto_20190714_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoffering',
            name='letter_grade_promotion_borderline',
            field=models.DecimalField(blank=True, decimal_places=4, default=0.0, help_text='This will be used to check students eligibility for letter grade promotion.', max_digits=10, null=True, verbose_name='Letter Grade Promotion Borderline Difference'),
        ),
    ]
