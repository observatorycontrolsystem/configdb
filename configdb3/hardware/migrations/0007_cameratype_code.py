# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0006_instrument_autoguider_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='cameratype',
            name='code',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
