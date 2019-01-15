from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
import datetime


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
    site = models.ForeignKey(Site)

    def __str__(self):
        return '{0}.{1}'.format(self.site, self.code)


class Telescope(BaseModel):
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)
    serial_number = models.CharField(max_length=50, default='', help_text='Unique telescope serial number')
    slew_rate = models.FloatField(help_text='The rate in sec/arcsec at which the telescope slews between positions')
    lat = models.FloatField()
    long = models.FloatField()
    horizon = models.FloatField()
    ha_limit_neg = models.FloatField()
    ha_limit_pos = models.FloatField()
    enclosure = models.ForeignKey(Enclosure)

    def __str__(self):
        return '{0}.{1}'.format(self.enclosure, self.code)


class Filter(BaseModel):
    FILTER_TYPES = (
        ("Standard", "Standard"),
        ("Engineering", "Engineering"),
        ("Slit", "Slit"),
        ("VirtualSlit", "VirtualSlit"),
        ("Exotic", "Exotic")
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    filter_type = models.CharField(max_length=200, choices=FILTER_TYPES, default="Standard")

    def __str__(self):
        return self.code


class FilterWheel(BaseModel):
    filters = models.ManyToManyField(Filter)

    def __str__(self):
        filters_str = ','.join([filter.code for filter in self.filters.all()])
        return filters_str


class OpticalElement(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    schedulable = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class OpticalElementGroup(BaseModel):
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    optical_elements = models.ManyToManyField(OpticalElement)
    element_change_overhead = models.FloatField(default=0)

    def __str__(self):
        optical_elements_str = self.name + ' - ' + self.type
        return optical_elements_str

    def optical_element_codes(self):
        return ','.join([oe.code for oe in self.optical_elements.all()])


class CameraType(BaseModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=200)
    default_mode = models.ForeignKey('Mode', null=True, blank=True)
    size = models.CharField(max_length=200)
    pscale = models.FloatField()
    fixed_overhead_per_exposure = models.FloatField(default=1)
    front_padding = models.FloatField(default=90)
    filter_change_time = models.FloatField(default=0)
    config_change_time = models.FloatField(default=0)
    acquire_exposure_time = models.FloatField(default=0)
    acquire_processing_time = models.FloatField(default=0)

    # New stuff for SOAR
    configuration_types = ArrayField(models.CharField(max_length=20))
    pixels_x = models.IntegerField(default=0)
    pixels_y = models.IntegerField(default=0)
    max_rois = models.IntegerField(default=0)
    default_acceptability_threshold = models.FloatField(default=90.0)

    def __str__(self):
        return self.code


class GenericMode(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    overhead = models.FloatField()
    params = JSONField(blank=True)
    default = models.BooleanField(default=False)
    camera_type = models.ForeignKey(CameraType, related_name='modes')

    def __str__(self):
        return '{} mode: {}'.format(self.type, self.name)

    def save(self, *args, **kwargs):
        if self.default:
            try:
                set_mode = GenericMode.objects.get(camera_type=self.camera_type, type=self.type, default=True)
                if self != set_mode:
                    set_mode.default = False
                    set_mode.save()
            except GenericMode.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class Mode(BaseModel):
    binning = models.IntegerField()
    overhead = models.IntegerField()
    readout = models.FloatField(default=0)
    camera_type = models.ForeignKey(CameraType)

    @property
    def binning_str(self):
        return '{0}x{0}'.format(self.binning)

    def __str__(self):
        return '{0}.{1}'.format(self.camera_type, self.binning_str)


class Camera(BaseModel):
    camera_type = models.ForeignKey(CameraType)
    code = models.CharField(max_length=200)
    filter_wheel = models.ForeignKey(FilterWheel)
    optical_element_groups = models.ManyToManyField(OpticalElementGroup)
    modes = models.ManyToManyField(GenericMode)
    host = models.CharField(max_length=200, default='',
                            help_text='The physical machine hostname that this camera is connected to')

    class Meta:
        ordering = ['code']

    @property
    def filters(self):
        return str(self.filter_wheel)

    @property
    def optical_elements(self):
        return {oeg.type: oeg.optical_element_codes() for oeg in self.optical_element_groups.all()}

    def __str__(self):
        return '{0}'.format(self.code)


class Instrument(BaseModel):
    DISABLED = 0
    ENABLED = 10
    COMMISSIONING = 20
    SCHEDULABLE = 30
    STATE_CHOICES = (
        (DISABLED, 'DISABLED'),
        (ENABLED, 'ENABLED'),
        (COMMISSIONING, 'COMMISSIONING'),
        (SCHEDULABLE, 'SCHEDULABLE'),
    )
    AUTOGUIDER_TYPES = (
        ("InCamera", "InCamera"),
        ("OffAxis", "OffAxis"),
        ("SelfGuide", "SelfGuide")
    )

    code = models.CharField(max_length=200, help_text='Name of the instrument')
    state = models.IntegerField(choices=STATE_CHOICES, default=DISABLED)
    telescope = models.ForeignKey(Telescope)
    science_camera = models.ForeignKey(Camera)
    autoguider_camera = models.ForeignKey(Camera, related_name='autoguides_for')
    autoguider_type = models.CharField(max_length=200, choices=AUTOGUIDER_TYPES, default="OffAxis")

    def __str__(self):
        return '{0}.{1}-{2}'.format(self.telescope, self.science_camera, self.autoguider_camera)
