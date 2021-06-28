from rest_framework import serializers
from cerberus import Validator

from .models import (
    Site, Enclosure, Telescope, OpticalElement, GenericMode, Instrument, Camera, OpticalElementGroup,
    CameraType, GenericModeGroup, InstrumentType, ConfigurationTypeProperties
)


class StateField(serializers.IntegerField):
    def to_internal_value(self, data):
        state_to_number = {choice[1]: choice[0] for choice in Instrument.STATE_CHOICES}
        if data.upper() in state_to_number.keys():
            return state_to_number[data.upper()]
        raise serializers.ValidationError('State {} is not valid. Valid states include [{}]'
                                          .format(data.upper(), ', '.join(state_to_number.keys())))

    def to_representation(self, value):
        number_to_state = {choice[0]: choice[1] for choice in Instrument.STATE_CHOICES}
        if value in number_to_state:
            return number_to_state[value]
        return None


class OpticalElementSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OpticalElement
        fields = ('name', 'code', 'schedulable')


class OpticalElementGroupSerializer(serializers.ModelSerializer):
    optical_elements = OpticalElementSerializer(many=True, help_text='Optical elements belonging to this optical element group')
    default = serializers.SerializerMethodField('get_default_code', help_text='Default optical element code')

    class Meta:
        model = OpticalElementGroup
        fields = ('name', 'type', 'optical_elements', 'element_change_overhead', 'default')
        depth = 1

    def get_default_code(self, obj):
        return obj.default.code if obj.default else ''

    def validate(self, data):
        if data['default'] not in [oe['code'] for oe in data['optical_elements']]:
            raise serializers.ValidationError("Default must be the code of an optical element in this group")

        return data


class GenericModeSerializer(serializers.ModelSerializer):
    validation_schema = serializers.JSONField(help_text='Cerberus styled validation schema used to validate '
                                                        'instrument configs using this generic mode')

    class Meta:
        fields = ('name', 'overhead', 'code', 'schedulable', 'validation_schema')
        model = GenericMode

    def validate_validation_schema(self, value):
        try:
            Validator(value)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid cerberus validation_schema: {repr(e)}")

        return value


class GenericModeGroupSerializer(serializers.ModelSerializer):
    modes = GenericModeSerializer(many=True, help_text='Set of modes belonging to this generic mode group')
    default = serializers.SerializerMethodField('get_default_code', help_text='Default mode within this generic mode group')

    class Meta:
        fields = ('type', 'modes', 'default')
        model = GenericModeGroup

    def get_default_code(self, obj):
        return obj.default.code if obj.default else ''

    def validate(self, data):
        if data['default'] not in [mode['code'] for mode in data['modes']]:
            raise serializers.ValidationError("Default must be the code of a mode in this group")

        return data


class CameraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'size', 'pscale', 'name', 'code', 'pixels_x', 'pixels_y', 'max_rois')
        model = CameraType


class CameraSerializer(serializers.ModelSerializer):
    camera_type = CameraTypeSerializer(read_only=True, help_text='Camera type')
    camera_type_id = serializers.IntegerField(write_only=True, help_text='Unique ID that corresponds to this camera\'s type')
    optical_element_groups = OpticalElementGroupSerializer(many=True, read_only=True, 
                                                           help_text='Optical element groups that this camera belongs to')

    class Meta:
        fields = ('id', 'code', 'camera_type', 'camera_type_id',
                  'optical_elements', 'optical_element_groups', 'host')
        model = Camera


class ConfigurationTypePropertiesSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='configuration_type.name', help_text='Configuration type name')
    code = serializers.ReadOnlyField(source='configuration_type.code', help_text='Configuration type code')

    class Meta:
        fields = ('name', 'code', 'config_change_overhead', 'schedulable', 'force_acquisition_off', 'requires_optical_elements')
        model = ConfigurationTypeProperties


class InstrumentTypeSerializer(serializers.ModelSerializer):
    mode_types = GenericModeGroupSerializer(many=True, required=False, help_text='Set of generic modes that this instrument type supports')
    configuration_types = ConfigurationTypePropertiesSerializer(source='configurationtypeproperties_set', many=True, required=False, read_only=True,
                                                                help_text='Set of configuration types that this instrument type supports')

    class Meta:
        fields = ('id', 'name', 'code', 'fixed_overhead_per_exposure', 'instrument_category',
                  'observation_front_padding', 'acquire_exposure_time',
                  'mode_types', 'default_acceptability_threshold', 'config_front_padding',
                  'allow_self_guiding', 'configuration_types', 'validation_schema')
        model = InstrumentType

    def validate_validation_schema(self, value):
        try:
            Validator(value)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid cerberus validation_schema: {repr(e)}")

        return value


class InstrumentSerializer(serializers.ModelSerializer):
    autoguider_camera = CameraSerializer(read_only=True, help_text='Autoguider camera for this instrument')
    autoguider_camera_id = serializers.IntegerField(write_only=True, 
                                                    help_text='Unique ID for the autoguider camera belonging to this instrument')
    telescope = serializers.HyperlinkedRelatedField(view_name='telescope-detail', read_only=True,
                                                    help_text='Telescope this instrument belongs to')
    telescope_id = serializers.IntegerField(write_only=True,
                                            help_text='Unique ID for the telescope that this instrument belongs to')
    science_cameras = CameraSerializer(read_only=True, many=True,
                                       help_text='Science cameras that belong to this instrument')
    science_cameras_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True, 
                                                             queryset=Camera.objects.all(), source='science_cameras',
                                                             help_text='Unique IDs for the science cameras belonging to this instrument')
    instrument_type = InstrumentTypeSerializer(read_only=True, help_text='Instrument type')
    instrument_type_id = serializers.IntegerField(write_only=True, help_text='Unique ID for the instrument type of this instrument')
    state = StateField(help_text='Instrument state')

    class Meta:
        fields = ('id', 'code', 'state', 'telescope', 'autoguider_camera_id',
                  'telescope_id', 'autoguider_camera', 'science_cameras', 'science_cameras_ids', 'instrument_type',
                  'instrument_type_id', '__str__')
        model = Instrument


class TelescopeSerializer(serializers.ModelSerializer):
    instrument_set = InstrumentSerializer(many=True, read_only=True, help_text='Set of instruments belonging to this telescope')
    enclosure = serializers.HyperlinkedRelatedField(view_name='enclosure-detail', read_only=True,
                                                    help_text='Enclosure that this telescope belongs to')
    enclosure_id = serializers.IntegerField(write_only=True, help_text='Unique IDs for the enclosure that this telescope belongs to')

    class Meta:
        fields = ('id', 'serial_number', 'name', 'code', 'active', 'lat', 'enclosure_id', 'slew_rate',
                  'minimum_slew_overhead', 'instrument_change_overhead', 'long', 'enclosure', 'horizon',
                  'ha_limit_pos', 'ha_limit_neg', 'zenith_blind_spot', 'instrument_set', '__str__')
        model = Telescope


class EnclosureSerializer(serializers.ModelSerializer):
    telescope_set = TelescopeSerializer(many=True, read_only=True, help_text='Set of telescopes within this enclosure')
    site = serializers.HyperlinkedRelatedField(view_name='site-detail', read_only=True,
                                               help_text='Site where this enclosure is located')
    site_id = serializers.IntegerField(write_only=True, help_text='Unique ID for the site this enclosure belongs to')

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'site', 'site_id',
                  'telescope_set', '__str__')
        model = Enclosure


class SiteSerializer(serializers.ModelSerializer):
    enclosure_set = EnclosureSerializer(many=True, read_only=True, help_text='Set of enclosures belonging to this site')

    class Meta:
        fields = (
            'id',
            'name',
            'code',
            'active',
            'timezone',
            'restart',
            'tz',
            'lat',
            'long',
            'elevation',
            'enclosure_set',
            '__str__',
        )
        model = Site
