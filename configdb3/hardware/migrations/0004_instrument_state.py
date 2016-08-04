# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-04 17:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0003_horizon_ha'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='state',
            field=models.IntegerField(choices=[(0, 'DISABLED'), (10, 'ENABLED'), (20, 'COMMISSIONING'), (30, 'SCHEDULABLE')], default=0),
        ),
    ]
