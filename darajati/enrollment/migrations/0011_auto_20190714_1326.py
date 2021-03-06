# Generated by Django 2.2.3 on 2019-07-14 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0010_auto_20190115_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructor',
            name='university_id',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='university id'),
        ),
        migrations.AlterField(
            model_name='student',
            name='university_id',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='university id'),
        ),
    ]
