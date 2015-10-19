# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0003_auto_20151019_2057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filterwheel',
            name='filters',
            field=models.CharField(unique=True, max_length=5000),
        ),
    ]
