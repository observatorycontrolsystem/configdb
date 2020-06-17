# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='CameraType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('code', models.CharField(max_length=200)),
                ('size', models.CharField(max_length=200)),
                ('pscale', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Enclosure',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('code', models.CharField(max_length=200)),
                ('name', models.CharField(default='', blank=True, max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=200)),
                ('filter_type', models.CharField(default='Standard', choices=[('Standard', 'Standard'), ('Engineering', 'Engineering'), ('Slit', 'Slit'), ('VirtualSlit', 'VirtualSlit'), ('Exotic', 'Exotic')], max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FilterWheel',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('filters', models.ManyToManyField(to='hardware.Filter')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('schedulable', models.BooleanField(default=True)),
                ('autoguider_type', models.CharField(default='OffAxis', choices=[('InCamera', 'InCamera'), ('OffAxis', 'OffAxis'), ('SelfGuide', 'SelfGuide')], max_length=200)),
                ('autoguider_camera', models.ForeignKey(related_name='autoguides_for', to='hardware.Camera', on_delete=models.CASCADE)),
                ('science_camera', models.ForeignKey(to='hardware.Camera', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Mode',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('binning', models.IntegerField()),
                ('overhead', models.IntegerField()),
                ('camera_type', models.ForeignKey(to='hardware.CameraType', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('code', models.CharField(max_length=3)),
                ('name', models.CharField(default='', blank=True, max_length=200)),
                ('timezone', models.IntegerField()),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Telescope',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('code', models.CharField(max_length=200)),
                ('name', models.CharField(default='', blank=True, max_length=200)),
                ('lat', models.FloatField()),
                ('long', models.FloatField()),
                ('enclosure', models.ForeignKey(to='hardware.Enclosure', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='instrument',
            name='telescope',
            field=models.ForeignKey(to='hardware.Telescope', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='enclosure',
            name='site',
            field=models.ForeignKey(to='hardware.Site', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='cameratype',
            name='default_mode',
            field=models.ForeignKey(blank=True, null=True, to='hardware.Mode', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='camera',
            name='camera_type',
            field=models.ForeignKey(to='hardware.CameraType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='camera',
            name='filter_wheel',
            field=models.ForeignKey(to='hardware.FilterWheel', on_delete=models.CASCADE),
        ),
    ]
