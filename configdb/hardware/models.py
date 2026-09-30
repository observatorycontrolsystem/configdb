import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator

class BaseModel(models.Model):
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Site(BaseModel):
    active = models.BooleanField(default=True, help_text='Whether the site is active and able to accept observations')
    code = models.CharField(max_length=3, help_text='3-letter site code')
    name = models.CharField(default='', blank=True, max_length=200, help_text='Site name')
    lat = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text='Site latitude in decimal degrees'
    )
    long = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text='Site longitude in decimal degrees'
    )
    elevation = models.IntegerField(
        # validator covers the extents of the terrestrial Earth
        validators=[MinValueValidator(-500), MaxValueValidator(100000)],
        help_text='Site elevation in meters'
    )
    # TODO FIXME:
    # The timezone field does not accurately represent the world. It is supposed
    # to represent the offset from UTC in hours. In many timezones, this changes
    # several times per year (US/Pacific varies between -7 and -8, depending on
    # daylight savings time). It is also incapable of representing many time zones
    # around the world that have non-Integer offsets (example: Australia/Adelaide).
    timezone = models.IntegerField(
        help_text='Offset from UTC in hours',
        validators=[MinValueValidator(-12), MaxValueValidator(14)]
    )
    tz = models.CharField(default='Etc/UTC', max_length=64, help_text='Timezone Name')
    restart = models.TimeField(default=datetime.time(hour=0, minute=0, second=0), help_text='Daily restart time in UTC')

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class Enclosure(BaseModel):
    active = models.BooleanField(default=True, help_text='Whether the enclosure is active and able to accept observations')
    code = models.CharField(max_length=200, help_text='Enclosure code')
    name = models.CharField(default='', blank=True, max_length=200, help_text='Enclosure name')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, help_text='Site where this enclosure is located')

    def __str__(self):
        return '{0}.{1}'.format(self.site, self.code)


class Telescope(BaseModel):
    active = models.BooleanField(default=True, help_text='Whether the telescope is active and able to accept observations')
    code = models.CharField(max_length=200, help_text='Telescope code')
    name = models.CharField(default='', blank=True, max_length=200, help_text='Telescome name')
    serial_number = models.CharField(max_length=50, default='', help_text='Unique telescope serial number')
    telescope_front_padding = models.FloatField(
        default=90,
        validators=[MinValueValidator(0)],
        help_text='Setup time for taking on observation on this telescope, applied once per '
        'observation. This is for an average of tasks like initial slewing and opening the enclosure.'
    )
    slew_rate = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='The rate in sec/arcsec at which the telescope slews between targets within a single observation'
    )
    minimum_slew_overhead = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='The minimum amount of time a slew can take in seconds for targets within a single observation'
    )
    instrument_change_overhead = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='The maximum amount of time it takes to switch instruments on this telescope'
    )
    lat = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text='Telescope latitude in decimal degrees'
    )
    long = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text='Telescope longitude in decimal degrees'
    )
    horizon = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(90)],
        help_text='Minimum distance from horizion telescope can point without field of view being obscured, in degrees'
    )
    aperture = models.FloatField(validators=[MinValueValidator(0)], default=0.0,
                                 help_text='The aperture of this telescope in meters. This is used to group telescopes by aperture class')
    ha_limit_neg = models.FloatField(validators=[MinValueValidator(-12), MaxValueValidator(0)],
                                     help_text='Negative hour-angle limit in hours')
    ha_limit_pos = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(12)],
                                     help_text='Positive hour-angle limit in hours')
    zenith_blind_spot = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(180)],
        help_text='For AltAz telescopes, radius of zenith blind spot in degrees'
    )
    enclosure = models.ForeignKey(Enclosure, on_delete=models.CASCADE, help_text='Enclosure which contains this telescope')

    def __str__(self):
        return '{0}.{1}'.format(self.enclosure, self.code)


class OpticalElement(BaseModel):
    name = models.CharField(max_length=200, help_text='Optical element name')
    code = models.CharField(max_length=200, unique=True, help_text='Optical element code')
    sky_flat_order = models.IntegerField(
        null=True, blank=True,
        help_text='Position of this element in the evening sky flat sequence, lowest first. The morning '
                  'sequence runs in reverse. Leave blank to take no sky flats through this element.'
    )
    sky_flat_cadence_days = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)],
        help_text='Target interval in days between sky flats through this element. Leave blank to take '
                  'sky flats through it only when nothing else is due. SkyFlatFilter overrides this per '
                  'instrument type.'
    )
    schedulable = models.BooleanField(
        default=True,
        help_text='Whether this optical element should be usable by scheduled observations, or only via direct submission.'
    )

    def __str__(self):
        return self.code


class OpticalElementGroup(BaseModel):
    name = models.CharField(max_length=200, help_text='Optical element group name')
    type = models.CharField(max_length=200, help_text='Optical element group type')
    default = models.ForeignKey(OpticalElement, related_name='default', null=True,
                                blank=True, on_delete=models.PROTECT, help_text='Default optical element within this optical element group')
    optical_elements = models.ManyToManyField(OpticalElement, help_text="Optical elements belonging to this optical element group")
    element_change_overhead = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Overhead in seconds when changing between optical elements within this optical element group'
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        optical_elements_str = self.name + ' - ' + self.type + ': ' + self.optical_element_codes()
        return optical_elements_str

    def optical_element_codes(self):
        return ','.join([oe.code for oe in self.optical_elements.all()])


class CameraType(BaseModel):
    name = models.CharField(max_length=200, unique=True, help_text='Camera type name')
    code = models.CharField(max_length=200, help_text='Camera type code')
    size = models.CharField(max_length=200, help_text='Field of view in arcminutes')
    pscale = models.FloatField(help_text='Pixel scale in arcseconds/pixel', validators=[MinValueValidator(0.0)])
    pixels_x = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Number of pixels on x-axis'
    )
    pixels_y = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Number of pixels on y-axis'
    )
    max_rois = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Maximum regions of interest that this camera type supports'
    )

    def __str__(self):
        return self.code


class ConfigurationType(BaseModel):
    code = models.CharField(max_length=64, primary_key=True, help_text='Configuration type code')
    name = models.CharField(max_length=200, help_text='Configuration type name')

    def __str__(self):
        return self.code


class InstrumentCategory(BaseModel):
    code = models.CharField(max_length=64, primary_key=True, help_text='Instrument category code')

    class Meta:
        verbose_name_plural = 'Instrument categories'

    def __str__(self):
        return self.code


class InstrumentType(BaseModel):
    name = models.CharField(max_length=200, help_text='Instrument type name')
    code = models.CharField(max_length=200, unique=True, help_text='Instrument type code')
    instrument_category = models.ForeignKey(
        InstrumentCategory, on_delete=models.PROTECT, null=True,
        help_text='The category of this instrument type, like IMAGE or SPECTRO. '
    )
    fixed_overhead_per_exposure = models.FloatField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text='A per exposure overhead to be applied. This accounts for any per exposure '
                  'setup or delays found in the camera or instrument control software.'
    )
    observation_front_padding = models.FloatField(
        default=90,
        validators=[MinValueValidator(0)],
        help_text='Setup time for taking on observation on this instrument, applied '
                  'once per observation. This is for tasks like initial slewing and instrument configuration.'
    )
    config_front_padding = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Setup time for each configuration of an observation on this instrument. '
                  'This is for things like configuration specific setup time.'
    )
    acquire_exposure_time = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='The default exposure time to use for acquisition exposures with this instrument type.'
    )
    configuration_types = models.ManyToManyField(
        ConfigurationType, through='ConfigurationTypeProperties',
        help_text='The set of configuration types available for use with this instrument type.'
    )
    default_configuration_type = models.ForeignKey(ConfigurationType, related_name='default_for',
        null=True, blank=True, on_delete=models.CASCADE,
        help_text='The default configuration type shown on the frontend or used if none is specified for this instrument type.'
    )
    default_acceptability_threshold = models.FloatField(
        default=90.0,
        validators=[MinValueValidator(0), MaxValueValidator(100.0)],
        help_text='The default acceptability threshold to use for Requests submitted on this instrument type. '
                  'Acceptability threshold is the minimum percentage of data an Observation must take before '
                  'causing its Request to be counted as complete.'
    )
    allow_self_guiding = models.BooleanField(default=True, blank=True,
                                             help_text='Whether to allow instruments of this type to be used for self-guiding'
                                             )
    validation_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text='Cerberus styled validation schema used to validate instrument configs using this instrument type'
    )

    def __str__(self):
        return self.code


class ConfigurationTypeProperties(BaseModel):
    configuration_type = models.ForeignKey(ConfigurationType, on_delete=models.CASCADE,
                                           help_text='Configuration type')
    instrument_type = models.ForeignKey(InstrumentType, on_delete=models.CASCADE,
                                        help_text='Instrument type')
    force_acquisition_off = models.BooleanField(
        default=False,
        help_text='If True, this configuration type will force the acquisition mode to be OFF. Certain configuration types '
                  'will not need acquisition, such as Biases, Darks, and potentially Lamp Flats and Arcs'
    )
    requires_optical_elements = models.BooleanField(
        default=True,
        help_text='Whether this configuration type requires optical path elements to be set. Some types like Biases and Darks '
                  'typically do not need these set, so this value should be false for those types.'
    )
    schedulable = models.BooleanField(
        default=True,
        help_text='Whether this configuration type should be usable by scheduled observations, or only via direct submission.'
    )
    config_change_overhead = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Time necessary for switching to this configuration type from a different configuration type during an '
                  'observation, like going between a Spectrum and a Lamp Flat for example. This could account for starting up '
                  'a lamp.'
    )
    validation_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text='Cerberus styled validation schema used to validate instrument configs using this configuration type and instrument type'
    )

    class Meta:
        unique_together = ('instrument_type', 'configuration_type')
        verbose_name_plural = 'Configuration type properties'

    def __str__(self):
        return f"{self.instrument_type.code}-{self.configuration_type.code}"


class ModeType(BaseModel):
    id = models.CharField(max_length=200, primary_key=True, help_text='Mode type')

    def __str__(self):
        return self.id


class GenericMode(BaseModel):
    name = models.CharField(max_length=200, help_text='Generic mode name')
    code = models.CharField(max_length=200, help_text='Generic mode code')
    overhead = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text='Overhead associated with the generic mode. Where this overhead is applied depends on what type '
                  'of generic mode this is for. For example, a readout mode is applied per exposure, while an acquisition '
                  'overhead is applied for the acquisition step at the beginning of an observation.'
    )
    schedulable = models.BooleanField(
        default=True,
        help_text='Whether this mode should be usable by scheduled observations, or only via direct submission.'
    )
    validation_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text='A cerberus styled validation schema that will be used to validate the structure this mode applies to'
    )

    def __str__(self):
        return '{}: {}'.format(self.code, self.name)


class GenericModeGroup(BaseModel):
    instrument_type = models.ForeignKey(InstrumentType, related_name='mode_types',
                                        null=True, on_delete=models.CASCADE,
                                        help_text='Instrument type')
    default = models.ForeignKey(GenericMode, related_name='default',
                                null=True, blank=True, on_delete=models.PROTECT,
                                help_text='Default mode within this generic mode group')
    type = models.ForeignKey(ModeType, null=True, on_delete=models.PROTECT, help_text='Generic mode group type')
    modes = models.ManyToManyField(GenericMode, help_text='Modes within this generic mode group')

    class Meta:
        unique_together = ['instrument_type', 'type']
        # TODO:: the unique_together should change to this in later versions of django
        # constraints = [
        #     models.constraints.UniqueConstraint(fields=['camera_type', 'type'], name='unique_mode_group')
        # ]

    def __str__(self):
        return ','.join([mode.code for mode in self.modes.all()])


class Camera(BaseModel):
    camera_type = models.ForeignKey(CameraType, on_delete=models.CASCADE, help_text='Camera type')
    code = models.CharField(max_length=200, help_text='Camera code')
    orientation = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(360.0)],
        help_text='The orientation of the Cameras ccd in degrees measured counterclockwise from North (y-axis)'
    )
    optical_element_groups = models.ManyToManyField(OpticalElementGroup, blank=True,
                                                    help_text='Optical element groups that this camera contains')
    host = models.CharField(max_length=200, default='', blank=True,
                            help_text='The physical machine hostname that this camera is connected to')

    class Meta:
        ordering = ['code']

    @property
    def optical_elements(self):
        return {oeg.type: oeg.optical_element_codes() for oeg in self.optical_element_groups.all()}

    def __str__(self):
        return '{0}'.format(self.code)


class Instrument(BaseModel):
    DISABLED = 'DISABLED'
    MANUAL = 'MANUAL'
    COMMISSIONING = 'COMMISSIONING'
    STANDBY = 'STANDBY'
    SCHEDULABLE = 'SCHEDULABLE'

    STATE_CHOICES = (
        (DISABLED, 'DISABLED'),
        (MANUAL, 'MANUAL'),
        (COMMISSIONING, 'COMMISSIONING'),
        (STANDBY, 'STANDBY'),
        (SCHEDULABLE, 'SCHEDULABLE'),
    )
    AUTOGUIDER_TYPES = (
        ("InCamera", "InCamera"),
        ("OffAxis", "OffAxis"),
        ("SelfGuide", "SelfGuide")
    )

    state_help_text = """<div><ul><li>DISABLED - The instrument is in configdb, but does not physically exist or is sitting in a box somewhere.</li>
    <li>MANUAL - The instrument is plugged in, but not ready to do any science.</li>
    <li>COMMISSIONING - The instrument is currently commissioning, but should not yet be exposed to the network.</li>
    <li>STANDBY - The instrument has been commissioned and is ready to be switched into SCHEDULABLE when needed.</li>
    <li>SCHEDULABLE - The instrument is part of the network and is ready for normal operations</li></ul></div>
    """
    instrument_type = models.ForeignKey(InstrumentType, null=True, on_delete=models.CASCADE, help_text='Instrument type')
    code = models.CharField(max_length=200, default='', blank=True, help_text='Instrument code')
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default='DISABLED', help_text=state_help_text)
    telescope = models.ForeignKey(Telescope, on_delete=models.CASCADE, help_text='Telescope this instrument belongs to')
    science_cameras = models.ManyToManyField(Camera, help_text='Science cameras that belong to this instrument')
    autoguider_camera = models.ForeignKey(Camera, related_name='autoguides_for', on_delete=models.CASCADE, help_text='Autoguider camera for this instrument')
    autoguider_type = models.CharField(max_length=200, choices=AUTOGUIDER_TYPES, default="OffAxis", help_text='Type of autoguider used on this instrument')

    def __str__(self):
        return '{0}.{1}'.format(self.telescope, self.code)


class FilterSet(BaseModel):
    name = models.CharField(max_length=100, unique=True, help_text='Filter set name')
    optical_elements = models.ManyToManyField(
        OpticalElement, help_text='Optical elements making up this set'
    )

    def __str__(self):
        return self.name


class SkyFlatFilter(BaseModel):
    instrument_type = models.ForeignKey(InstrumentType, on_delete=models.CASCADE,
                                        help_text='Instrument type this override applies to')
    optical_element = models.ForeignKey(OpticalElement, on_delete=models.CASCADE,
                                        help_text='Optical element this override applies to')
    order = models.IntegerField(
        null=True, blank=True,
        help_text='Overrides OpticalElement.sky_flat_order for this instrument type.'
    )
    cadence_days = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)],
        help_text='Overrides OpticalElement.sky_flat_cadence_days for this instrument type.'
    )

    class Meta:
        unique_together = ('instrument_type', 'optical_element')

    def __str__(self):
        return f'{self.instrument_type.code}-{self.optical_element.code}'


class CalibrationTarget(BaseModel):
    name = models.CharField(max_length=200, help_text='Target name')
    ra = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(360.0)],
        help_text='Right ascension in degrees'
    )
    dec = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text='Declination in degrees'
    )
    proper_motion_ra = models.FloatField(null=True, blank=True, help_text='Proper motion in RA, mas/year')
    proper_motion_dec = models.FloatField(null=True, blank=True, help_text='Proper motion in Dec, mas/year')
    configuration_type = models.ForeignKey(ConfigurationType, on_delete=models.PROTECT,
                                           help_text='Configuration type this target is used for')
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.CASCADE,
                             help_text='Restrict this target to one site. Leave blank for any site.')
    season_start = models.CharField(max_length=5, blank=True,
                                    help_text='MM-DD, inclusive. Leave blank for all year.')
    season_end = models.CharField(max_length=5, blank=True,
                                  help_text='MM-DD, inclusive. Leave blank for all year.')
    config = models.JSONField(
        default=dict, blank=True,
        help_text='Per-target overrides such as exposure time, slit, max airmass and acquire radius.'
    )

    def __str__(self):
        return f'{self.name} ({self.configuration_type_id})'


class CalibrationSchedule(BaseModel):
    """What the calibration poller submits, and with what settings.

    Scope has two independent axes. A location, being at most one of instrument,
    telescope or site, and an optional instrument_type qualifier. A lookup takes
    the most specific row that matches and fills any value left blank from the
    next row out.

    Location is ranked first, so a row naming a site beats one naming only an
    instrument type. That is what lets operations stop a calibration at one site
    without editing the network-wide defaults.
    """
    EVENING = 'EVENING'
    MORNING = 'MORNING'
    BOTH = 'BOTH'
    WHEN_CHOICES = ((EVENING, 'Evening'), (MORNING, 'Morning'), (BOTH, 'Both'))

    # Location axis, most specific first. At most one may be set on a row.
    LOCATION_FIELDS = ('instrument', 'telescope', 'site')
    SCOPE_FIELDS = LOCATION_FIELDS + ('instrument_type',)
    VALUE_FIELDS = ('filter_set', 'exposures_per_run', 'exposure_time', 'cadence_days',
                    'sun_alt_start', 'sun_alt_end', 'proposal', 'window_offset_minutes',
                    'window_count', 'window_length_minutes')

    configuration_type = models.ForeignKey(ConfigurationType, on_delete=models.PROTECT,
                                           help_text='Configuration type to submit')

    instrument = models.ForeignKey('Instrument', null=True, blank=True, on_delete=models.CASCADE,
                                   help_text='Scope this row to a single instrument')
    telescope = models.ForeignKey(Telescope, null=True, blank=True, on_delete=models.CASCADE,
                                  help_text='Scope this row to a telescope, letting the submitter pick the instrument')
    instrument_type = models.ForeignKey(InstrumentType, null=True, blank=True, on_delete=models.CASCADE,
                                        help_text='Scope this row to an instrument type')
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.CASCADE,
                             help_text='Scope this row to a site')

    enabled = models.BooleanField(default=True, help_text='Uncheck to stop submitting without deleting the row')
    when = models.CharField(max_length=8, choices=WHEN_CHOICES, default=BOTH,
                            help_text='Which twilight this run belongs to')
    direct_submission = models.BooleanField(
        default=True,
        help_text='Place the observation directly through /api/schedule/, which takes the slot. '
                  'Uncheck to queue it through /api/requestgroups/ and let the scheduler decide. '
                  'AUTO_FOCUS runs both ways, so a row of each can exist at the same scope.'
    )
    readout_modes = models.ManyToManyField(
        GenericMode, blank=True,
        help_text='Readout modes this run covers. Leave empty for every mode the instrument has.'
    )

    filter_set = models.ForeignKey(FilterSet, null=True, blank=True, on_delete=models.PROTECT,
                                   help_text='Filter set to observe through')
    exposures_per_run = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)],
                                            help_text='Number of exposures per run')
    exposure_time = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)],
                                      help_text='Exposure time in seconds')
    cadence_days = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)],
                                       help_text='Target interval in days between runs')
    sun_alt_start = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Solar altitude in degrees at which the window opens'
    )
    sun_alt_end = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Solar altitude in degrees at which the window closes'
    )
    proposal = models.CharField(
        max_length=64, blank=True,
        help_text='Portal proposal to submit under. Leave blank for the default for this configuration '
                  'type. Set it only to change priority, as elp does with rescue_auto_focus.'
    )
    window_offset_minutes = models.IntegerField(
        null=True, blank=True,
        help_text='Delay the window opening this many minutes past the point sun_alt_start '
                  'is reached. The observing window, not the submission.'
    )
    window_count = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)],
        help_text='How many windows to offer. Leave blank to tile until sun_alt_end is '
                  'reached, which is what routine autofocus does today.'
    )
    window_length_minutes = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)],
        help_text='Length of each window. Leave blank for a single window spanning '
                  'sun_alt_start to sun_alt_end, which is what every calibration except '
                  'the queued autofocus uses.'
    )

    class Meta:
        unique_together = ('configuration_type', 'instrument', 'telescope', 'instrument_type',
                           'site', 'when', 'direct_submission')

    def clean(self):
        locations = [f for f in self.LOCATION_FIELDS if getattr(self, f'{f}_id', None)]
        if len(locations) > 1:
            raise ValidationError(
                f'Set at most one location. This row sets {", ".join(locations)}. '
                f'An instrument type can be combined with any one of them.'
            )

    @property
    def specificity(self):
        """Sort key, lowest first. Location outranks the instrument type qualifier."""
        location = next(
            (i for i, f in enumerate(self.LOCATION_FIELDS) if getattr(self, f'{f}_id', None)),
            len(self.LOCATION_FIELDS)
        )
        return (location, 0 if self.instrument_type_id else 1)

    @classmethod
    def matching(cls, instrument, configuration_type, direct_submission, when=BOTH):
        """Rows that apply to this instrument, most specific first.

        Disabled rows are included so that a narrow row can switch off what a
        broader one turns on. Use effective() to get the answer that counts.
        """
        site = instrument.telescope.enclosure.site
        rows = cls.objects.filter(
            configuration_type=configuration_type, direct_submission=direct_submission
        ).filter(
            Q(when=when) | Q(when=cls.BOTH)
        ).filter(
            Q(instrument=instrument) | Q(instrument__isnull=True)
        ).filter(
            Q(telescope=instrument.telescope) | Q(telescope__isnull=True)
        ).filter(
            Q(site=site) | Q(site__isnull=True)
        ).filter(
            Q(instrument_type=instrument.instrument_type) | Q(instrument_type__isnull=True)
        )
        # A row naming this twilight beats one that covers both at the same scope.
        return sorted(rows, key=lambda r: (r.specificity, r.when == cls.BOTH))

    @classmethod
    def effective(cls, instrument, configuration_type, direct_submission, when=BOTH):
        """Merged settings for this instrument, or None if nothing should be submitted.

        Values come from the most specific row that sets them, so a per-instrument
        row can override one setting and inherit the rest. The most specific row
        also decides whether anything runs at all, so a site row with enabled off
        suppresses an instrument type row that is on.
        """
        rows = cls.matching(instrument, configuration_type, direct_submission, when)
        if not rows or not rows[0].enabled:
            return None
        settings = {}
        for row in rows:
            for field in cls.VALUE_FIELDS:
                if settings.get(field) in (None, ''):
                    settings[field] = getattr(row, field)
        # An empty set means every mode, so it inherits like any other blank value
        # rather than widening a narrow row back to the full set.
        settings['readout_modes'] = []
        for row in rows:
            modes = list(row.readout_modes.all())
            if modes:
                settings['readout_modes'] = modes
                break
        return settings

    def __str__(self):
        parts = [str(getattr(self, f)) for f in self.SCOPE_FIELDS if getattr(self, f'{f}_id', None)]
        how = 'direct' if self.direct_submission else 'queued'
        return f'{self.configuration_type_id} on {" ".join(parts) or "network"} ({self.when.lower()}, {how})'
