# Generated by Django 4.0.3 on 2023-02-24 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0034_copy_instrument_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurationtypeproperties',
            name='validation_schema',
            field=models.JSONField(blank=True, default=dict, help_text='Cerberus styled validation schema used to validate instrument configs using this configuration type and instrument type'),
        ),
    ]
