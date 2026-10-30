import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.comparison


class Migration(migrations.Migration):

    dependencies = [
        ("hardware", "0037_calibration_schedule_help_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="calibrationschedule",
            name="elements_per_run",
            field=models.IntegerField(
                blank=True,
                help_text="How many optical element and readout mode combinations one run covers, "
                          "taking the most overdue first. Blank covers every combination the "
                          "instrument has.",
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name="opticalelement",
            name="sky_flat_cadence_days",
            field=models.IntegerField(
                blank=True,
                help_text="Target interval in days between sky flats through this element. Leave blank to take "
                          "sky flats through it only when nothing else is due. SkyFlatFilter overrides this per "
                          "instrument type, and SkyFlatReadout overrides both for a readout mode.",
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.CreateModel(
            name="SkyFlatReadout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "cadence_days",
                    models.IntegerField(
                        help_text="Target interval in days between sky flats in this readout mode, through any "
                                  "optical element. Overrides SkyFlatFilter and OpticalElement cadences.",
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "instrument_type",
                    models.ForeignKey(
                        help_text="Instrument type this override applies to",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hardware.instrumenttype",
                    ),
                ),
                (
                    "readout_mode",
                    models.ForeignKey(
                        help_text="Readout mode this override applies to",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hardware.genericmode",
                    ),
                ),
            ],
            options={
                "unique_together": {("instrument_type", "readout_mode")},
            },
        ),
        migrations.AlterUniqueTogether(
            name="calibrationschedule",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="calibrationschedule",
            constraint=models.UniqueConstraint(
                models.F("configuration_type"),
                django.db.models.functions.comparison.Coalesce(models.F("instrument"), models.Value(0)),
                django.db.models.functions.comparison.Coalesce(models.F("telescope"), models.Value(0)),
                django.db.models.functions.comparison.Coalesce(models.F("instrument_type"), models.Value(0)),
                django.db.models.functions.comparison.Coalesce(models.F("site"), models.Value(0)),
                models.F("when"),
                models.F("direct_submission"),
                name="unique_calibration_schedule_scope",
                violation_error_message="A row with this configuration type, scope, twilight and submission "
                                        "path already exists.",
            ),
        ),
    ]
