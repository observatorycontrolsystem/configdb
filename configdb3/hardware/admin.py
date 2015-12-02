from django.contrib import admin
from configdb3.hardware.models import (
    Site, Enclosure, Filter,
    Telescope, Instrument, Camera, CameraType, Mode,
    FilterWheel
)


class HardwareAdmin(admin.ModelAdmin):
    exclude = ('modified', )


@admin.register(Site)
class SiteAdmin(HardwareAdmin):
    list_display = ('code', 'active', 'name', 'timezone')
    search_fields = ('code', 'active', 'name', 'timezone')
    list_filter = ('active',)


@admin.register(Enclosure)
class EnclosureAdmin(HardwareAdmin):
    list_display = ('__str__', 'active', 'name')
    list_filter = ('site__code', 'active')
    search_fields = ('code', 'name', 'active', 'site__code')


@admin.register(Telescope)
class TelescopeAdmin(HardwareAdmin):
    list_display = ('__str__', 'active', 'name', 'lat', 'long')
    list_filter = ('enclosure__site__code',)
    search_fields = ('code', 'name', 'active', 'enclosure__site__code')


@admin.register(Instrument)
class InstrumentAdmin(HardwareAdmin):
    list_display = ('__str__', 'schedulable', 'telescope', 'science_camera', 'autoguider_camera')
    list_filter = ('telescope__enclosure__site__code', 'schedulable')


@admin.register(Camera)
class CameraAdmin(HardwareAdmin):
    list_display = ('code', 'camera_type')
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
    list_display = ('id', '__str__',)


@admin.register(Filter)
class FilterAdmin(HardwareAdmin):
    list_display = ('name', 'code', 'filter_type')
    search_fields = ('name',)
