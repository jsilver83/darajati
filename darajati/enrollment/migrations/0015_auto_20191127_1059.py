# Generated by Django 2.2.3 on 2019-11-27 07:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0014_auto_20191103_1212'),
    ]

    operations = [
        migrations.RenameField(
            model_name='courseoffering',
            old_name='auto_grade_promotion_difference',
            new_name='auto_grade_promotion_delta',
        ),
    ]
