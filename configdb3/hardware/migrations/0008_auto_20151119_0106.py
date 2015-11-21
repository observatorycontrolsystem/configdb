# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0007_cameratype_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('basemodel_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hardware.BaseModel')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=200)),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.RemoveField(
            model_name='filterwheel',
            name='filters',
        ),
        migrations.AddField(
            model_name='filterwheel',
            name='filters',
            field=models.ManyToManyField(to='hardware.Filter'),
        ),
    ]
