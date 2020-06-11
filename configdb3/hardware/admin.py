from datetime import timedelta

from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION, ADDITION, CHANGE
from django.utils.html import escape
from django.urls import reverse
from django import forms
from django.core.exceptions import ValidationError
from reversion.models import Version
from reversion.admin import VersionAdmin
from reversion.errors import RegistrationError

from configdb3.hardware.models import (
    Site, Enclosure, GenericMode, ModeType, GenericModeGroup, Telescope, Instrument, Camera, CameraType,
    OpticalElementGroup, OpticalElement
)


class GenericModeGroupAdminForm(forms.ModelForm):
    class Meta:
        model = GenericModeGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        existing = 'instance' in kwargs and kwargs['instance']
        super().__init__(*args, **kwargs)
        if existing:
            self.fields['default'].queryset = self.instance.modes.all()


class OpticalElementGroupAdminForm(forms.ModelForm):
    class Meta:
        model = OpticalElementGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        existing = 'instance' in kwargs and kwargs['instance']
        super().__init__(*args, **kwargs)
        if existing:
            self.fields['default'].queryset = self.instance.optical_elements.all()


class CameraAdminForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = '__all__'

    def clean(self):
        if 'optical_element_groups' in self.cleaned_data:
            group_types = [oeg.type for oeg in self.cleaned_data['optical_element_groups'].all()]
            if len(group_types) != len(set(group_types)):
                raise ValidationError("Can only have 1 optical element group of each type associated with a Camera")

        return self.cleaned_data


class HardwareAdmin(VersionAdmin):
    exclude = ('modified', )


@admin.register(ModeType)
class ModeTypeAdmin(HardwareAdmin):
    list_display = ('id',)


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
    list_display = ('__str__', 'state', 'telescope', 'code', 'science_camera', 'autoguider_camera')
    list_filter = ('telescope__enclosure__site__code', 'state')


@admin.register(Camera)
class CameraAdmin(HardwareAdmin):
    form = CameraAdminForm
    list_display = ('code', 'camera_type')
    search_fields = ('code',)


@admin.register(CameraType)
class CameraTypeAdmin(HardwareAdmin):
    list_display = ('name', 'size', 'pscale', 'allow_self_guiding')
    search_fields = ('name',)


@admin.register(GenericModeGroup)
class GenericModeGroupAdmin(HardwareAdmin):
    form = GenericModeGroupAdminForm
    list_display = ('camera_type', 'type', 'default', '__str__')
    search_fields = ('camera_type', 'type')
    list_filter = ('type', 'camera_type')


@admin.register(GenericMode)
class GenericModeAdmin(HardwareAdmin):
    list_display = ('name', 'code', 'overhead')
    search_fields = ('name', 'code')


@admin.register(OpticalElementGroup)
class OpticalElementGroupAdmin(HardwareAdmin):
    form = OpticalElementGroupAdminForm
    list_display = ('id', 'name', 'type', '__str__', 'default')
    search_fields = ('name', 'type')
    list_filter = ('type',)


@admin.register(OpticalElement)
class OpticalElementAdmin(HardwareAdmin):
    list_display = ('name', 'code', 'schedulable')
    search_fields = ('name', 'code')


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
                reverse('admin:{0}_{1}_recoverlist'.format(ct.app_label, ct.model))
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
                    reverse('admin:{0}_{1}_recover'.format(ct.app_label, ct.model), args=[versions[0].id])
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
