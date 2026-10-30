import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("hardware", "0036_calibration_scheduling"),
    ]

    operations = [
        migrations.AlterField(
            model_name="calibrationschedule",
            name="sun_alt_end",
            field=models.FloatField(
                blank=True,
                help_text="The darker of the two. Leave blank to anchor the window at sun_alt_start and size it from the exposures instead, which is what bias and dark do.",
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(-90),
                    django.core.validators.MaxValueValidator(90),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="calibrationschedule",
            name="sun_alt_start",
            field=models.FloatField(
                blank=True,
                help_text="The brighter of the two solar altitudes bounding the window. An evening window opens here, a morning window closes here.",
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(-90),
                    django.core.validators.MaxValueValidator(90),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="calibrationschedule",
            name="telescope",
            field=models.ForeignKey(
                blank=True,
                help_text="Scope this row to a telescope, covering every instrument on it",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="hardware.telescope",
            ),
        ),
    ]
