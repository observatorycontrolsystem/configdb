from datetime import timedelta
import json

from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION, ADDITION, CHANGE
from django.utils.html import escape
from django.urls import reverse
from django import forms
from django.core.exceptions import ValidationError
from reversion.models import Version
from reversion.admin import VersionAdmin
from reversion.errors import RegistrationError

from configdb.hardware.heroic import update_heroic_instrument_capabilities
from configdb.hardware.models import (
    Site, Enclosure, GenericMode, ModeType, GenericModeGroup, Telescope, Instrument, Camera, CameraType,
    OpticalElementGroup, OpticalElement, InstrumentType, InstrumentCategory, ConfigurationType, ConfigurationTypeProperties
)
from configdb.hardware.validator import OCSValidator


class ProperJSONField(forms.JSONField):
    """ To allow validation_schema JSONFields in the admin interface to accept empty dict {}"""
    empty_values= [None, "", [], ()]


class PrettyJSONEncoder(json.JSONEncoder):
    """ To pretty print the json validation_schema in the admin interface forms """
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=2, sort_keys=True, **kwargs)


class ConfigurationTypePropertiesAdminForm(forms.ModelForm):
    validation_schema = ProperJSONField(encoder=PrettyJSONEncoder)

    class Meta:
        model = ConfigurationTypeProperties
        fields = '__all__'


class GenericModeAdminForm(forms.ModelForm):
    validation_schema = ProperJSONField(encoder=PrettyJSONEncoder)

    class Meta:
        model = GenericMode
        fields = '__all__'


class GenericModeGroupAdminForm(forms.ModelForm):
    class Meta:
        model = GenericModeGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        existing = 'instance' in kwargs and kwargs['instance']
        super().__init__(*args, **kwargs)
        if existing:
            self.fields['default'].queryset = self.instance.modes.all()

    def clean(self):
        if 'validation_schema' in self.cleaned_data:
            try:
                OCSValidator(self.cleaned_data['validation_schema'])
            except Exception as e:
                raise ValidationError(f"Invalid cerberus validation_schema: {repr(e)}")

        return self.cleaned_data


class OpticalElementGroupAdminForm(forms.ModelForm):
    class Meta:
        model = OpticalElementGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        existing = 'instance' in kwargs and kwargs['instance']
        super().__init__(*args, **kwargs)
        if existing:
            self.fields['default'].queryset = self.instance.optical_elements.all()


class InstrumentTypeAdminForm(forms.ModelForm):
    validation_schema = ProperJSONField(encoder=PrettyJSONEncoder)

    class Meta:
        model = InstrumentType
        fields = '__all__'

    def clean(self):
        if 'validation_schema' in self.cleaned_data:
            try:
                OCSValidator(self.cleaned_data['validation_schema'])
            except Exception as e:
                raise ValidationError(f"Invalid cerberus validation_schema: {repr(e)}")

        return self.cleaned_data


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


@admin.register(InstrumentCategory)
class InstrumentCategoryAdmin(HardwareAdmin):
    list_display = ('code',)


@admin.register(ConfigurationType)
class ConfigurationTypeAdmin(HardwareAdmin):
    list_display = ('code',)


@admin.register(ConfigurationTypeProperties)
class ConfigurationTypePropertiesAdmin(HardwareAdmin):
    form = ConfigurationTypePropertiesAdminForm
    list_display = ('configuration_type', 'instrument_type', 'schedulable', 'config_change_overhead', 'force_acquisition_off', 'requires_optical_elements')
    list_filter = ('schedulable', 'configuration_type__code', 'instrument_type__code')
    search_fields = ['configuration_type__code', 'instrument_type__code']


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
    list_display = ('__str__', 'active', 'name', 'lat', 'long', 'aperture')
    list_filter = ('enclosure__site__code',)
    search_fields = ('code', 'name', 'active', 'enclosure__site__code', 'aperture')


@admin.register(Instrument)
class InstrumentAdmin(HardwareAdmin):
    list_display = ('__str__', 'state', 'telescope', 'code', 'instrument_type', 'science_camera_codes', 'autoguider_camera')
    list_filter = ('telescope__enclosure__site__code', 'state')

    def science_camera_codes(self, obj):
        return ','.join([science_camera.code for science_camera in obj.science_cameras.all()])

    def save_related(self, request, form, formsets, change):
        # This is the best way to trigger on saving m2m admin relationships on the Instrument, like Science Cameras
        finished = super().save_related(request, form, formsets, change)
        update_heroic_instrument_capabilities(form.instance)
        return finished

@admin.register(Camera)
class CameraAdmin(HardwareAdmin):
    form = CameraAdminForm
    list_display = ('code', 'camera_type')
    search_fields = ('code',)

    def save_related(self, request, form, formsets, change):
        # This is the best way to trigger on saving m2m admin relationships on the Camera, like Optical Element Groups
        old_oegs = set(form.instance.optical_element_groups.all())
        finished = super().save_related(request, form, formsets, change)
        if old_oegs != set(form.instance.optical_element_groups.all()):
            for instrument in form.instance.instrument_set.all():
                update_heroic_instrument_capabilities(instrument)
        return finished


@admin.register(InstrumentType)
class InstrumentTypeAdmin(HardwareAdmin):
    form = InstrumentTypeAdminForm
    list_display = ('name', 'code', 'instrument_category', 'allow_self_guiding')
    search_fields = ('name',)
    list_filter = ('instrument_category', 'allow_self_guiding')


@admin.register(CameraType)
class CameraTypeAdmin(HardwareAdmin):
    list_display = ('name', 'size', 'pscale')
    search_fields = ('name',)


@admin.register(GenericModeGroup)
class GenericModeGroupAdmin(HardwareAdmin):
    form = GenericModeGroupAdminForm
    list_display = ('instrument_type', 'type', 'default', '__str__')
    search_fields = ('instrument_type', 'type')
    list_filter = ('type', 'instrument_type')

    def save_model(self, request, obj, form, change):
        old_instrument_type = None
        if obj.pk:
            old_obj = self.model.objects.get(pk=obj.pk)
            if old_obj.instrument_type != obj.instrument_type:
                old_instrument_type = old_obj.instrument_type
        # Now update the model so the new model details are saved
        finished = super().save_model(request, obj, form, change)

        if old_instrument_type:
            # The instrument_type has changed so update heroic for the old instrument type
            for instrument in old_instrument_type.instrument_set.all():
                update_heroic_instrument_capabilities(instrument)
        return finished

    def save_related(self, request, form, formsets, change):
        # This is the best way to trigger on saving m2m admin relationships on the GenericModeGroup,
        # like when its members change
        finished = super().save_related(request, form, formsets, change)
        if form.instance.instrument_type:
            for instrument in form.instance.instrument_type.instrument_set.all():
                update_heroic_instrument_capabilities(instrument)
        return finished


@admin.register(GenericMode)
class GenericModeAdmin(HardwareAdmin):
    form = GenericModeAdminForm
    list_display = ('name', 'code', 'overhead', 'schedulable')
    search_fields = ('name', 'code')

    def save_related(self, request, form, formsets, change):
        # This is the best way to trigger on saving m2m admin relationships on the GenericMode,
        # like when its membersships change
        finished = super().save_related(request, form, formsets, change)
        for gmg in form.instance.genericmodegroup_set.all():
            if gmg.instrument_type:
                for instrument in gmg.instrument_type.instrument_set.all():
                    update_heroic_instrument_capabilities(instrument)
        return finished


@admin.register(OpticalElementGroup)
class OpticalElementGroupAdmin(HardwareAdmin):
    form = OpticalElementGroupAdminForm
    list_display = ('id', 'name', 'type', '__str__', 'default')
    search_fields = ('name', 'type')
    list_filter = ('type',)

    def save_related(self, request, form, formsets, change):
        # This is the best way to trigger on saving m2m admin relationships on the OpticalElementGroup,
        # like when its members change
        finished = super().save_related(request, form, formsets, change)
        for camera in form.instance.camera_set.all():
            for instrument in camera.instrument_set.all():
                update_heroic_instrument_capabilities(instrument)
        return finished


@admin.register(OpticalElement)
class OpticalElementAdmin(HardwareAdmin):
    list_display = ('name', 'code', 'schedulable')
    search_fields = ('name', 'code')

    def save_related(self, request, form, formsets, change):
        # This is the best way to trigger on saving m2m admin relationships on the OpticalElement,
        # like when its memberships change
        finished = super().save_related(request, form, formsets, change)
        for oeg in form.instance.opticalelementgroup_set.all():
            for camera in oeg.camera_set.all():
                for instrument in camera.instrument_set.all():
                    update_heroic_instrument_capabilities(instrument)
        return finished


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
