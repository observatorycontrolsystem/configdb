from django.contrib import admin
from configdb3.hardware.models import (
    Site, Enclosure,
    Telescope, Instrument, Camera, CameraType, Mode,
    FilterWheel
)


class HardwareAdmin(admin.ModelAdmin):
    exclude = ('modified',)


@admin.register(Site)
class SiteAdmin(HardwareAdmin):
    list_display = ('code', 'name', 'timezone')
    search_fields = ('code', 'name', 'timezone')


@admin.register(Enclosure)
class EnclosureAdmin(HardwareAdmin):
    list_display = ('__str__', 'name')
    list_filter = ('site__code',)
    search_fields = ('code', 'name', 'site__code')


@admin.register(Telescope)
class TelescopeAdmin(HardwareAdmin):
    list_display = ('__str__', 'name', 'lat', 'long')
    list_filter = ('enclosure__site__code',)
    search_fields = ('code', 'name', 'enclosure__site__code')


@admin.register(Instrument)
class InstrumentAdmin(HardwareAdmin):
    list_display = ('__str__', 'telescope', 'science_camera', 'autoguider_camera')
    list_filter = ('telescope__enclosure__site__code',)


@admin.register(Camera)
class CameraAdmin(HardwareAdmin):
    list_display = ('code', 'camera_type', 'filters')
    search_fields = ('code',)


@admin.register(CameraType)
class CameraTypeAdmin(HardwareAdmin):
    list_display = ('name', 'size', 'pscale', 'default_mode')
    search_fields = ('name',)


@admin.register(Mode)
class ModeAdmin(HardwareAdmin):
    list_display = ('camera_type', 'binning', 'overhead')


@admin.register(FilterWheel)
class FilterWheelAdmin(HardwareAdmin):
    list_display = ('id', 'filters')
    search_fields = ('filters',)
