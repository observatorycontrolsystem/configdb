# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0009_instrument_schedulable'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='filter_type',
            field=models.CharField(default=b'Standard', max_length=200, choices=[(b'Standard', b'Standard'), (b'Engineering', b'Engineering'), (b'Slit', b'Slit'), (b'VirtualSlit', b'VirtualSlit'), (b'Exotic', b'Exotic')]),
        ),
    ]
