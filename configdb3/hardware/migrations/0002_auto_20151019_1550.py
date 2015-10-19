# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='site',
            options={'ordering': ['code']},
        ),
        migrations.RenameField(
            model_name='camera',
            old_name='name',
            new_name='code',
        ),
    ]
