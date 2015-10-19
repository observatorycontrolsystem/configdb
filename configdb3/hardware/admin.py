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
    pass


@admin.register(Enclosure)
class EnclosureAdmin(HardwareAdmin):
    pass


@admin.register(Telescope)
class TelescopeAdmin(HardwareAdmin):
    pass


@admin.register(Instrument)
class InstrumentAdmin(HardwareAdmin):
    pass


@admin.register(Camera)
class CameraAdmin(HardwareAdmin):
    pass


@admin.register(CameraType)
class CameraTypeAdmin(HardwareAdmin):
    pass


@admin.register(Mode)
class ModeAdmin(HardwareAdmin):
    pass


@admin.register(FilterWheel)
class FilterWheelAdmin(HardwareAdmin):
    pass
