from rest_framework import serializers

from .models import (
    Site, Enclosure, Telescope, OpticalElement, GenericMode, Instrument, Camera, OpticalElementGroup,
    CameraType, GenericModeGroup, InstrumentType, ConfigurationTypeProperties, ConfigurationType, ModeType,
    InstrumentCategory
)
from configdb.hardware.validator import OCSValidator
from configdb.hardware.heroic import update_heroic_instrument_capabilities


class OpticalElementSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpticalElement
        fields = ('id', 'name', 'code', 'schedulable')
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Update done so update HEROIC here - this catches optical elements name, code, or schedulability changes
        if 'name' in validated_data or 'code' in validated_data or 'schedulable' in validated_data:
            for oeg in instance.opticalelementgroup_set.all():
                for camera in oeg.camera_set.all():
                    for instrument in camera.instrument_set.all():
                        update_heroic_instrument_capabilities(instrument)
        return instance


class OpticalElementNestedSerializer(OpticalElementSerializer):
    # This nested serializer allows us to choose an existing optical element for the group
    # Since the groups create method will use get_or_create to link optical elements
    class Meta(OpticalElementSerializer.Meta):
        extra_kwargs = {
            'code': {
                'validators': [],
            }
        }


class OpticalElementGroupSerializer(serializers.ModelSerializer):
    optical_elements = OpticalElementNestedSerializer(
        many=True, required=False,
        help_text='Optical elements belonging to this optical element group'
    )
    optical_element_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=OpticalElement.objects.all(), required=False, write_only=True,
        help_text='Existing Optical Element ids to attach to this group'
    )
    default = serializers.SlugRelatedField(slug_field='code', queryset=OpticalElement.objects.all(), required=False,
                                           help_text='Default optical element code')

    class Meta:
        model = OpticalElementGroup
        fields = ('id', 'name', 'type', 'optical_elements', 'optical_element_ids', 'element_change_overhead', 'default')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('default', None) is None:
            data['default'] = ''
        return data

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        oe_codes = []
        if instance:
            oe_codes = [oe.code for oe in instance.optical_elements.all()]
        else:
            if 'optical_elements' in data:
                oe_codes.extend([oe['code'] for oe in data['optical_elements']])
            if 'optical_element_ids' in data:
                oe_codes.extend([oe.code for oe in data['optical_element_ids']])
        if ('default' in data and data['default'].code not in oe_codes):
            raise serializers.ValidationError(f"Default optical element {data['default']} must be a member of this groups optical elements")
        return super().validate(data)

    def create(self, validated_data):
        optical_elements = validated_data.pop('optical_elements', [])
        optical_element_instances = validated_data.pop('optical_element_ids', [])
        optical_element_group = super().create(validated_data)

        for optical_element_instance in optical_element_instances:
            optical_element_group.optical_elements.add(optical_element_instance)

        for optical_element in optical_elements:
            optical_element_instance, _ = OpticalElement.objects.get_or_create(code=optical_element.pop('code'), defaults=optical_element)
            optical_element_group.optical_elements.add(optical_element_instance)

        return optical_element_group

    def update(self, instance, validated_data):
        optical_elements = validated_data.pop('optical_elements', [])
        optical_element_instances = validated_data.pop('optical_element_ids', [])
        instance = super().update(instance, validated_data)
        if (optical_elements or optical_element_instances):
            instance.optical_elements.clear()  # If we are updating optical elements, clear out old optical elements first
        for optical_element_instance in optical_element_instances:
            instance.optical_elements.add(optical_element_instance)

        for optical_element in optical_elements:
            optical_element_instance, _ = OpticalElement.objects.get_or_create(code=optical_element.pop('code'), defaults=optical_element)
            instance.optical_elements.add(optical_element_instance)
        # Update done so update HEROIC here - this catches optical elements changes in the optical elements group
        if optical_elements or optical_element_instances or 'default' in validated_data or 'type' in validated_data:
            for camera in instance.camera_set.all():
                for instrument in camera.instrument_set.all():
                    update_heroic_instrument_capabilities(instrument)
        return instance


class ModeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id',)
        model = ModeType


class InstrumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('code',)
        model = InstrumentCategory


class GenericModeSerializer(serializers.ModelSerializer):
    validation_schema = serializers.JSONField(required=False, default=dict,
                                              help_text='Cerberus styled validation schema used to validate '
                                                        'instrument configs using this generic mode')

    class Meta:
        fields = ('id', 'name', 'overhead', 'code', 'schedulable', 'validation_schema')
        model = GenericMode
        read_only_fields = ['id']

    def validate_validation_schema(self, value):
        try:
            OCSValidator(value)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid cerberus validation_schema: {repr(e)}")

        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Update done so update HEROIC here - this catches generic mode name, code, or schedulability updates
        if 'name' in validated_data or 'code' in validated_data or 'schedulable' in validated_data:
            for gmg in instance.genericmodegroup_set.all():
                if gmg.instrument_type:
                    for instrument in gmg.instrument_type.instrument_set.all():
                        update_heroic_instrument_capabilities(instrument)
        return instance


class GenericModeGroupSerializer(serializers.ModelSerializer):
    instrument_type = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=InstrumentType.objects.all(),
        help_text='ID for the instrument type associated with this group'
    )
    modes = GenericModeSerializer(many=True, required=False,
                                  help_text='Set of modes belonging to this generic mode group')
    mode_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=GenericMode.objects.all(), required=False,
                                                  write_only=True, help_text='Existing mode ids to attach to this group')
    default = serializers.SlugRelatedField(slug_field='code', queryset=GenericMode.objects.all(), required=False,
                                           help_text='Default mode within this generic mode group')

    class Meta:
        fields = ('id', 'type', 'modes', 'mode_ids', 'default', 'instrument_type')
        model = GenericModeGroup

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('default', None) is None:
            data['default'] = ''
        return data

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        mode_codes = []
        if instance:
            mode_codes = [mode.code for mode in instance.modes.all()]
        else:
            if 'modes' in data:
                mode_codes.extend([mode['code'] for mode in data['modes']])
            if 'mode_ids' in data:
                mode_codes.extend([mode.code for mode in data['mode_ids']])
        if ('default' in data and data['default'].code not in mode_codes):
            raise serializers.ValidationError(f"Default generic mode {data['default']} must be a member of this groups modes")
        return super().validate(data)

    def create(self, validated_data):
        generic_modes = validated_data.pop('modes', [])
        generic_mode_instances = validated_data.pop('mode_ids', [])
        generic_mode_group = super().create(validated_data)

        for generic_mode_instance in generic_mode_instances:
            generic_mode_group.modes.add(generic_mode_instance)

        for generic_mode in generic_modes:
            generic_mode_instance, _ = GenericMode.objects.get_or_create(**generic_mode)
            generic_mode_group.modes.add(generic_mode_instance)

        # Update heroic when a new GenericModeGroup is created for the first time for an instrument_type
        for instrument in generic_mode_group.instrument_type.instrument_set.all():
            update_heroic_instrument_capabilities(instrument)
        return generic_mode_group

    def update(self, instance, validated_data):
        old_instrument_type = None
        generic_modes = validated_data.pop('modes', [])
        generic_mode_instances = validated_data.pop('mode_ids', [])
        if 'instrument_type' in validated_data and validated_data['instrument_type'] != instance.instrument_type:
            # In this special case, we need to update instruments of this old instrument type at the end
            old_instrument_type = instance.instrument_type
        instance = super().update(instance, validated_data)
        if (generic_modes or generic_mode_instances):
            instance.modes.clear()  # If we are updating modes, clear out old modes first
        for generic_mode_instance in generic_mode_instances:
            instance.modes.add(generic_mode_instance)

        for generic_mode in generic_modes:
            generic_mode_instance, _ = GenericMode.objects.get_or_create(**generic_mode)
            instance.modes.add(generic_mode_instance)
        # Update done so update HEROIC here - this catches generic mode changes in the generic mode group
        if instance.instrument_type and (generic_modes or generic_mode_instances or 'default' in validated_data or 'type' in validated_data):
            for instrument in instance.instrument_type.instrument_set.all():
                update_heroic_instrument_capabilities(instrument)
        if old_instrument_type:
            # Also update instruments of this old instrument type since they will have lost this generic mode group
            for instrument in Instrument.objects.filter(instrument_type=old_instrument_type):
                update_heroic_instrument_capabilities(instrument)
        return instance


class CameraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'size', 'pscale', 'name', 'code', 'pixels_x', 'pixels_y', 'max_rois')
        model = CameraType


class CameraSerializer(serializers.ModelSerializer):
    camera_type = CameraTypeSerializer(read_only=True, help_text='Camera type')
    camera_type_id = serializers.IntegerField(write_only=True, help_text='Model ID number that corresponds to this camera\'s type')
    optical_element_groups = OpticalElementGroupSerializer(many=True, read_only=True,
                                                           help_text='Optical element groups that this camera contains')
    optical_element_group_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True,
                                                             queryset=OpticalElementGroup.objects.all(), source='optical_element_groups',
                                                             help_text='Model ID numbers for the optical element groups belonging to this camera')

    class Meta:
        fields = ('id', 'code', 'camera_type', 'camera_type_id', 'orientation',
                  'optical_elements', 'optical_element_groups', 'optical_element_group_ids', 'host')
        model = Camera

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Update done so update HEROIC here - this catches optical element group changes on the camera
        if 'optical_element_groups' in validated_data or 'optical_element_group_ids' in validated_data:
            for instrument in instance.instrument_set.all():
                update_heroic_instrument_capabilities(instrument)
        return instance


class ConfigurationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'code')
        model = ConfigurationType


class ConfigurationTypePropertiesNestedSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='configuration_type.name', help_text='Configuration type name')
    code = serializers.ReadOnlyField(source='configuration_type.code', help_text='Configuration type code')
    configuration_type = serializers.PrimaryKeyRelatedField(queryset=ConfigurationType.objects.all(), write_only=True, required=False)

    class Meta:
        fields = ('name', 'code', 'configuration_type', 'config_change_overhead',
                  'schedulable', 'force_acquisition_off', 'requires_optical_elements', 'validation_schema')
        model = ConfigurationTypeProperties


class ConfigurationTypePropertiesSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'configuration_type', 'instrument_type', 'config_change_overhead',
                  'schedulable', 'force_acquisition_off', 'requires_optical_elements', 'validation_schema')
        model = ConfigurationTypeProperties


class InstrumentTypeSerializer(serializers.ModelSerializer):
    mode_types = GenericModeGroupSerializer(many=True, required=False, help_text='Set of generic modes that this instrument type supports')
    configuration_types = ConfigurationTypePropertiesNestedSerializer(
        source='configurationtypeproperties_set', many=True, required=False,
        help_text='Set of configuration types that this instrument type supports'
    )
    class Meta:
        fields = ('id', 'name', 'code', 'fixed_overhead_per_exposure', 'instrument_category',
                  'observation_front_padding', 'acquire_exposure_time', 'default_configuration_type',
                  'mode_types', 'default_acceptability_threshold', 'config_front_padding',
                  'allow_self_guiding', 'configuration_types', 'validation_schema')
        model = InstrumentType

    def validate_validation_schema(self, value):
        try:
            OCSValidator(value)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid cerberus validation_schema: {repr(e)}")

        return value

    def update(self, instance, validated_data):
        if 'configurationtypeproperties_set' in validated_data:
            configuration_type_properties = validated_data.pop('configurationtypeproperties_set')
            # Clear all existing configuration type properties if we are setting a new set on an update
            instance.configuration_types.all().delete()
            for configuration_type_property in configuration_type_properties:
                ConfigurationTypeProperties.objects.get_or_create(instrument_type=instance, **configuration_type_property)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        configuration_type_properties = validated_data.pop('configurationtypeproperties_set', [])
        instrument_type = InstrumentType.objects.create(**validated_data)

        for configuration_type_property in configuration_type_properties:
            ConfigurationTypeProperties.objects.get_or_create(instrument_type=instrument_type, **configuration_type_property)

        return instrument_type


class InstrumentSerializer(serializers.ModelSerializer):
    autoguider_camera = CameraSerializer(read_only=True, help_text='Autoguider camera for this instrument')
    autoguider_camera_id = serializers.IntegerField(write_only=True,
                                                    help_text='Model ID number for the autoguider camera belonging to this instrument')
    telescope = serializers.HyperlinkedRelatedField(view_name='telescope-detail', read_only=True,
                                                    help_text='Telescope this instrument belongs to')
    telescope_id = serializers.IntegerField(write_only=True,
                                            help_text='Model ID number for the telescope that this instrument belongs to')
    science_cameras = CameraSerializer(read_only=True, many=True,
                                       help_text='Science cameras that belong to this instrument')
    science_cameras_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True,
                                                             queryset=Camera.objects.all(), source='science_cameras',
                                                             help_text='Model ID numbers for the science cameras belonging to this instrument')
    instrument_type = InstrumentTypeSerializer(read_only=True, help_text='Instrument type')
    instrument_type_id = serializers.IntegerField(write_only=True, help_text='Model ID number for the instrument type of this instrument')
    state = serializers.ChoiceField(choices=Instrument.STATE_CHOICES, help_text='Instrument state')

    class Meta:
        fields = ('id', 'code', 'state', 'telescope', 'autoguider_camera_id',
                  'telescope_id', 'autoguider_camera', 'science_cameras', 'science_cameras_ids', 'instrument_type',
                  'instrument_type_id', '__str__')
        model = Instrument

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Update done so update HEROIC here - this catches state or camera changes on the instrument
        update_heroic_instrument_capabilities(instance)
        return instance


class TelescopeSerializer(serializers.ModelSerializer):
    instrument_set = InstrumentSerializer(many=True, read_only=True, help_text='Set of instruments belonging to this telescope')
    enclosure = serializers.HyperlinkedRelatedField(view_name='enclosure-detail', read_only=True,
                                                    help_text='Enclosure that this telescope belongs to')
    enclosure_id = serializers.IntegerField(write_only=True, help_text='Model ID number for the enclosure that this telescope belongs to')

    class Meta:
        fields = ('id', 'serial_number', 'name', 'code', 'active', 'aperture', 'lat', 'enclosure_id', 'slew_rate',
                  'minimum_slew_overhead', 'instrument_change_overhead', 'long', 'enclosure', 'horizon',
                  'ha_limit_pos', 'ha_limit_neg', 'telescope_front_padding', 'zenith_blind_spot', 'instrument_set', '__str__')
        model = Telescope


class EnclosureSerializer(serializers.ModelSerializer):
    telescope_set = TelescopeSerializer(many=True, read_only=True, help_text='Set of telescopes within this enclosure')
    site = serializers.HyperlinkedRelatedField(view_name='site-detail', read_only=True,
                                               help_text='Site where this enclosure is located')
    site_id = serializers.IntegerField(write_only=True, help_text='Model ID number for the site this enclosure belongs to')

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


class AvailabilityHistorySerializer(serializers.Serializer):
    instrument_id = serializers.CharField(required=True, write_only=True)
    telescope_id = serializers.CharField(required=True, write_only=True)
    site_id = serializers.CharField(required=True, write_only=True)
    enclosure_id = serializers.CharField(required=True, write_only=True)
    # Start/end are optional parameters to cap what is returned
    start = serializers.DateTimeField(required=False, write_only=True)
    end = serializers.DateTimeField(required=False, write_only=True)
    availability_intervals = serializers.DictField(read_only=True)
