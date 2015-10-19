# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseModel',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('name', models.CharField(max_length=200)),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='CameraType',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('name', models.CharField(max_length=200)),
                ('size', models.CharField(max_length=200)),
                ('pscale', models.FloatField()),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='Enclosure',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('code', models.CharField(max_length=200)),
                ('name', models.CharField(default='', blank=True, max_length=200)),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='FilterWheel',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('filters', models.CharField(max_length=5000)),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('autoguider_camera', models.ForeignKey(related_name='autoguides_for', to='hardware.Camera')),
                ('science_camera', models.ForeignKey(to='hardware.Camera')),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='Mode',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('binning', models.IntegerField()),
                ('overhead', models.IntegerField()),
                ('camera_type', models.ForeignKey(to='hardware.CameraType')),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('code', models.CharField(max_length=3)),
                ('name', models.CharField(default='', blank=True, max_length=200)),
                ('timezone', models.IntegerField()),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.CreateModel(
            name='Telescope',
            fields=[
                ('basemodel_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='hardware.BaseModel', auto_created=True)),
                ('code', models.CharField(max_length=200)),
                ('name', models.CharField(default='', blank=True, max_length=200)),
                ('lat', models.FloatField()),
                ('long', models.FloatField()),
                ('enclosure', models.ForeignKey(to='hardware.Enclosure')),
            ],
            bases=('hardware.basemodel',),
        ),
        migrations.AddField(
            model_name='instrument',
            name='telescope',
            field=models.ForeignKey(to='hardware.Telescope'),
        ),
        migrations.AddField(
            model_name='enclosure',
            name='site',
            field=models.ForeignKey(to='hardware.Site'),
        ),
        migrations.AddField(
            model_name='cameratype',
            name='default_mode',
            field=models.ForeignKey(null=True, blank=True, to='hardware.Mode'),
        ),
        migrations.AddField(
            model_name='camera',
            name='camera_type',
            field=models.ForeignKey(to='hardware.CameraType'),
        ),
        migrations.AddField(
            model_name='camera',
            name='filter_wheel',
            field=models.ForeignKey(to='hardware.FilterWheel'),
        ),
    ]
