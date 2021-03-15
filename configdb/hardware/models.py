import datetime

from django.db import models
from django.contrib.postgres.fields import JSONField


class BaseModel(models.Model):
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Site(BaseModel):
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=3)
    name = models.CharField(default='', blank=True, max_length=200)
    lat = models.FloatField(default=0.0)
    long = models.FloatField(default=0.0)
    elevation = models.IntegerField(help_text='meters')
    # TODO FIXME:
    # The timezone field does not accurately represent the world. It is supposed
    # to represent the offset from UTC in hours. In many timezones, this changes
    # several times per year (US/Pacific varies between -7 and -8, depending on
    # daylight savings time). It is also incapable of representing many time zones
    # around the world that have non-Integer offsets (example: Australia/Adelaide).
    timezone = models.IntegerField()
    tz = models.CharField(default='Etc/UTC', max_length=64, help_text='Timezone Name')
    restart = models.TimeField(default=datetime.time(hour=0, minute=0, second=0))

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class Enclosure(BaseModel):
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    def __str__(self):
        return '{0}.{1}'.format(self.site, self.code)


class Telescope(BaseModel):
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)
    serial_number = models.CharField(max_length=50, default='', help_text='Unique telescope serial number')
    slew_rate = models.FloatField(default=0,
                                  help_text='The rate in sec/arcsec at which the telescope slews between positions')
    minimum_slew_overhead = models.FloatField(default=0,
                                              help_text='The minimum amount of time a slew can take in seconds')
    instrument_change_overhead = models.FloatField(
        default=0, help_text='The maximum amount of time it takes to switch instruments')
    lat = models.FloatField()
    long = models.FloatField()
    horizon = models.FloatField()
    ha_limit_neg = models.FloatField()
    ha_limit_pos = models.FloatField()
    zenith_blind_spot = models.FloatField(
        default=0.0, help_text='For AltAz telescopes, radius of zenith blind spot in degrees')
    enclosure = models.ForeignKey(Enclosure, on_delete=models.CASCADE)

    def __str__(self):
        return '{0}.{1}'.format(self.enclosure, self.code)


class OpticalElement(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    schedulable = models.BooleanField(
        default=True,
        help_text='Whether this optical element should be usable by scheduled observations, or only via direct submission.'
    )

    def __str__(self):
        return self.code


class OpticalElementGroup(BaseModel):
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    default = models.ForeignKey(OpticalElement, related_name='default', null=True, blank=True, on_delete=models.PROTECT)
    optical_elements = models.ManyToManyField(OpticalElement)
    element_change_overhead = models.FloatField(default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        optical_elements_str = self.name + ' - ' + self.type + ': ' + self.optical_element_codes()
        return optical_elements_str

    def optical_element_codes(self):
        return ','.join([oe.code for oe in self.optical_elements.all()])


class CameraType(BaseModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=200)
    size = models.CharField(max_length=200)
    pscale = models.FloatField()
    pixels_x = models.IntegerField(default=0)
    pixels_y = models.IntegerField(default=0)
    max_rois = models.IntegerField(default=0)

    def __str__(self):
        return self.code

class ConfigurationType(BaseModel):
    code = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=200)
    schedulable = models.BooleanField(
        default=True,
        help_text='Whether this configuration type should be usable by scheduled observations, or only via direct submission.'
    )
    config_change_overhead = models.FloatField(
        default=0,
        help_text='Time necessary for switching to this configuration type from a different configuration type during an '
                  'observation, like going between a Spectrum and a Lamp Flat for example. This could account for starting up '
                  'a lamp.'
    )

    def __str__(self):
        return self.code

class InstrumentCategory(BaseModel):
    code = models.CharField(max_length=64, primary_key=True)

    def __str__(self):
        return self.code

class InstrumentType(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    instrument_category = models.ForeignKey(
        InstrumentCategory, on_delete=models.PROTECT, null=True,
        help_text='The category of this instrument type, like IMAGE or SPECTRO. '
    )
    fixed_overhead_per_exposure = models.FloatField(
        default=1,
        help_text='A per exposure overhead to be applied. This accounts for any per exposure '
                  'setup or delays found in the camera or instrument control software.'
    )
    observation_front_padding = models.FloatField(
        default=90,
        help_text='Setup time for taking on observation on this instrument, applied '
                  'once per observation. This is for tasks like slewing and instrument configuration.'
    )
    config_front_padding = models.FloatField(
        default=0,
        help_text='Setup time for each configuration of an observation on this instrument. '
                  'This is for things like configuration specific setup time.'
    )
    acquire_exposure_time = models.FloatField(
        default=0,
        help_text='The default exposure time to use for acquisition exposures with this instrument type.'
    )
    configuration_types = models.ManyToManyField(
        ConfigurationType, related_name='instrument_types',
        help_text='The set of configuration types available for use with this instrument type.'
    )
    default_acceptability_threshold = models.FloatField(
        default=90.0,
        help_text='The default acceptability threshold to use for Requests submitted on this instrument type. '
                  'Acceptability threshold is the minimum percentage of data an Observation must take before '
                  'causing its Request to be counted as complete.'
    )
    allow_self_guiding = models.BooleanField(default=True, blank=True)
    validation_schema = JSONField(default=dict, blank=True,
                                  help_text='Cerberus styled validation schema used to validate instrument configs using this instrument type'
                                  )

    def __str__(self):
        return self.code


class ModeType(BaseModel):
    id = models.CharField(max_length=200, primary_key=True)

    def __str__(self):
        return self.id


class GenericMode(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    overhead = models.FloatField(
        help_text='Overhead associated with the generic mode. Where this overhead is applied depends on what type '
                  'of generic mode this is for. For example, a readout mode is applied per exposure, while an acquisition '
                  'overhead is applied for the acquisition step at the beginning of an observation.'
    )
    schedulable = models.BooleanField(
        default=True,
        help_text='Whether this mode should be usable by scheduled observations, or only via direct submission.'
    )
    validation_schema = JSONField(default=dict, blank=True,
        help_text='A cerberus styled validation schema that will be used to validate the structure this mode applies to'
    )

    def __str__(self):
        return '{}: {}'.format(self.code, self.name)


class GenericModeGroup(BaseModel):
    instrument_type = models.ForeignKey(InstrumentType, related_name='mode_types', null=True, on_delete=models.CASCADE)
    default = models.ForeignKey(GenericMode, related_name='default', null=True, blank=True, on_delete=models.PROTECT)
    type = models.ForeignKey(ModeType, null=True, on_delete=models.PROTECT)
    modes = models.ManyToManyField(GenericMode)

    class Meta:
        unique_together = ['instrument_type', 'type']
        # TODO:: the unique_together should change to this in later versions of django
        # constraints = [
        #     models.constraints.UniqueConstraint(fields=['camera_type', 'type'], name='unique_mode_group')
        # ]

    def __str__(self):
        return ','.join([mode.code for mode in self.modes.all()])


class Camera(BaseModel):
    camera_type = models.ForeignKey(CameraType, on_delete=models.CASCADE)
    code = models.CharField(max_length=200)
    optical_element_groups = models.ManyToManyField(OpticalElementGroup, blank=True)
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
    DISABLED = 0
    MANUAL = 10
    COMMISSIONING = 20
    STANDBY = 25
    SCHEDULABLE = 30
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
    instrument_type = models.ForeignKey(InstrumentType, null=True, on_delete=models.CASCADE)
    code = models.CharField(max_length=200, default='', blank=True, help_text='Name of the instrument')
    state = models.IntegerField(choices=STATE_CHOICES, default=DISABLED, help_text=state_help_text)
    telescope = models.ForeignKey(Telescope, on_delete=models.CASCADE)
    science_cameras = models.ManyToManyField(Camera)
    autoguider_camera = models.ForeignKey(Camera, related_name='autoguides_for', on_delete=models.CASCADE)
    autoguider_type = models.CharField(max_length=200, choices=AUTOGUIDER_TYPES, default="OffAxis")

    def __str__(self):
        return '{0}.{1}'.format(self.telescope, self.code)
