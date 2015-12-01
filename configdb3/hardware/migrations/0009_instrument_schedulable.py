# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0008_auto_20151119_0106'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='schedulable',
            field=models.BooleanField(default=True),
        ),
    ]
