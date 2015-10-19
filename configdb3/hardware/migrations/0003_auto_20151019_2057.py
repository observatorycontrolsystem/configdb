# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0002_auto_20151019_1550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cameratype',
            name='name',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
