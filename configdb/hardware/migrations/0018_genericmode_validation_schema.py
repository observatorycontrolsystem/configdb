# Generated by Django 3.0.6 on 2020-06-08 06:26

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0017_auto_20200521_0229'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericmode',
            name='validation_schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text='A cerberus styled validation schema that will be used to validate the structure this mode applies to'),
        ),
    ]
