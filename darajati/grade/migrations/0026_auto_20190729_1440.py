# Generated by Django 2.2.3 on 2019-07-29 11:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0025_auto_20190725_1405'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gradefragment',
            old_name='letter_grade_promotion_criterion',
            new_name='grade_promotion_criterion',
        ),
    ]
