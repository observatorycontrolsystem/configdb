# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0004_auto_20151019_2137'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='camera',
            options={'ordering': ['code']},
        ),
    ]
