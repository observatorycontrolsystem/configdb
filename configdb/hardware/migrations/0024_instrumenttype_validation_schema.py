# Generated by Django 3.0.12 on 2021-02-10 21:09

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0023_auto_20200709_0718'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrumenttype',
            name='validation_schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text='Cerberus styled validation schema used to validate instrument configs using this instrument type'),
        ),
    ]
