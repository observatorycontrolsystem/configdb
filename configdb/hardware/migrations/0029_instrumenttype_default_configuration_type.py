# Generated by Django 3.0.6 on 2021-11-11 22:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0028_auto_20210721_0650'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrumenttype',
            name='default_configuration_type',
            field=models.ForeignKey(blank=True, help_text='The default configuration type shown on the frontend or used if none is specified for this instrument type.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='default_for', to='hardware.ConfigurationType'),
        ),
    ]