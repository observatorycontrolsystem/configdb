# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-02-13 21:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0013_auto_20190201_2351'),
    ]

    operations = [
        migrations.AddField(
            model_name='cameratype',
            name='allow_self_guiding',
            field=models.BooleanField(default=True),
        ),
    ]
