from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION, ADDITION, CHANGE
from reversion.models import Version
from datetime import timedelta
from django.utils.html import escape
from django.core.urlresolvers import reverse
from reversion.admin import VersionAdmin
from reversion.errors import RegistrationError
from configdb3.hardware.models import (
    Site, Enclosure, Filter,
    Telescope, Instrument, Camera, CameraType, Mode,
    FilterWheel
)


class HardwareAdmin(VersionAdmin):
    exclude = ('modified', )


@admin.register(Site)
class SiteAdmin(HardwareAdmin):
    list_display = ('code', 'active', 'name', 'timezone', 'elevation')
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
    list_display = ('__str__', 'state', 'telescope', 'science_camera', 'autoguider_camera')
    list_filter = ('telescope__enclosure__site__code', 'state')


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


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = 'action_time'

    readonly_fields = [f.name for f in LogEntry._meta.get_fields()]

    list_filter = [
        'user',
        'content_type',
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'recover_link',
        'change_message',
        'action',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def recover_link(self, obj):
        ct = obj.content_type
        if obj.action_flag == DELETION:
            link = '<a href="{0}">Recover deleted objects</a>'.format(
                reverse('admin:{0}_{1}_recoverlist'.format(ct.app_label, ct.model)),
                escape(obj.object_repr)
            )
        else:
            try:
                versions = Version.objects.get_for_object(obj.get_edited_object()).filter(
                    # hacky but gets the version for this object just before it was saved
                    revision__date_created__lte=obj.action_time - timedelta(seconds=1)
                )
            except RegistrationError:
                return 'Revision control not supported by this type'

            if versions:
                link = '<a href="{0}">View Previous Version</a>'.format(
                    reverse('admin:{0}_{1}_recover'.format(ct.app_label, ct.model), args=[versions[0].id]),
                )
            else:
                link = 'No previous versions'
        return link
    recover_link.allow_tags = True

    def object_link(self, obj):
        ct = obj.content_type
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            link = '<a href="{0}">{1}</a>'.format(
                reverse('admin:{0}_{1}_change'.format(ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = 'object'

    def action(self, obj):
        if obj.action_flag == DELETION:
            return 'Deleted'
        elif obj.action_flag == ADDITION:
            return 'Created'
        elif obj.action_flag == CHANGE:
            return 'Updated'
        else:
            return ''

    def queryset(self, request):
        return super().queryset(request).prefetch_related('content_type')
