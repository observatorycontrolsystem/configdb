from django.db import models


class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    modified = models.DateTimeField(auto_now=True)


class Site(BaseModel):
    code = models.CharField(max_length=3)
    name = models.CharField(default='', blank=True, max_length=200)
    timezone = models.IntegerField()

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class Enclosure(BaseModel):
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)
    site = models.ForeignKey(Site)

    def __str__(self):
        return '{0}.{1}'.format(self.site, self.code)


class Telescope(BaseModel):
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)
    lat = models.FloatField()
    long = models.FloatField()
    enclosure = models.ForeignKey(Enclosure)

    def __str__(self):
        return '{0}.{1}'.format(self.enclosure, self.code)


class FilterWheel(BaseModel):
    filters = models.CharField(max_length=5000, unique=True)

    def __str__(self):
        return self.filters


class CameraType(BaseModel):
    name = models.CharField(max_length=200, unique=True)
    default_mode = models.ForeignKey('Mode', null=True, blank=True)
    size = models.CharField(max_length=200)
    pscale = models.FloatField()

    def __str__(self):
        return self.name


class Mode(BaseModel):
    binning = models.IntegerField()
    overhead = models.IntegerField()
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

    class Meta:
        ordering = ['code']

    @property
    def filters(self):
        return self.filter_wheel.filters

    def __str__(self):
        return '{0}'.format(self.code)


class Instrument(BaseModel):
    telescope = models.ForeignKey(Telescope)
    science_camera = models.ForeignKey(Camera)
    autoguider_camera = models.ForeignKey(Camera, related_name='autoguides_for')

    @property
    def autoguider_type(self):
        if self.science_camera == self.autoguider_camera:
            return 'SelfGuide'
        else:
            return 'OffAxis'

    def __str__(self):
        return '{0}.{1}-{2}'.format(self.telescope, self.science_camera, self.autoguider_camera)
