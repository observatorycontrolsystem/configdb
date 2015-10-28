# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0005_auto_20151020_1801'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='autoguider_type',
            field=models.CharField(default='OffAxis', max_length=200, choices=[('InCamera', 'InCamera'), ('OffAxis', 'OffAxis'), ('SelfGuide', 'SelfGuide')]),
        ),
    ]
