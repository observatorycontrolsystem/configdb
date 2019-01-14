from rest_framework import serializers
from .models import (Site, Enclosure, Telescope, OpticalElement,
                     Instrument, Camera, Mode, OpticalElementGroup,
                     FilterWheel, CameraType, Filter)


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
    optical_elements = OpticalElementSerializer(many=True)

    class Meta:
        model = OpticalElementGroup
        fields = ('id', 'name', 'type', 'optical_elements', 'element_change_overhead')
        depth = 1


class FilterSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'code', 'filter_type')
        model = Filter
        depth = 1


class FilterWheelSerializer(serializers.ModelSerializer):
    filters = FilterSerializer(many=True)

    class Meta:
        fields = ('id', 'filters', '__str__')
        model = FilterWheel
        depth = 1


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'binning', 'overhead', 'readout')
        model = Mode


class CameraTypeSerializer(serializers.ModelSerializer):
    default_mode = ModeSerializer()
    mode_set = ModeSerializer(many=True)

    class Meta:
        fields = ('id', 'size', 'pscale', 'default_mode', 'name', 'code', 'mode_set', 'fixed_overhead_per_exposure',
                  'front_padding', 'filter_change_time', 'config_change_time', 'acquire_exposure_time',
                  'acquire_processing_time')
        model = CameraType


class CameraSerializer(serializers.ModelSerializer):
    camera_type = CameraTypeSerializer(read_only=True)
    camera_type_id = serializers.IntegerField(write_only=True)
    filter_wheel_id = serializers.IntegerField(write_only=True)
    filter_wheel = FilterWheelSerializer(read_only=True)
    optical_element_groups = OpticalElementGroupSerializer(many=True, read_only=True)

    class Meta:
        fields = ('id', 'code', 'camera_type', 'camera_type_id', 'filter_wheel', 'filter_wheel_id', 'filters',
                  'optical_elements', 'optical_element_groups')
        model = Camera


class InstrumentSerializer(serializers.ModelSerializer):
    science_camera = CameraSerializer(read_only=True)
    science_camera_id = serializers.IntegerField(write_only=True)
    autoguider_camera = CameraSerializer(read_only=True)
    autoguider_camera_id = serializers.IntegerField(write_only=True)
    telescope = serializers.HyperlinkedRelatedField(view_name='telescope-detail', read_only=True)
    telescope_id = serializers.IntegerField(write_only=True)

    state = StateField()

    class Meta:
        fields = ('id', 'state', 'telescope', 'science_camera', 'science_camera_id', 'autoguider_camera_id',
                  'telescope_id', 'autoguider_camera', '__str__')
        model = Instrument


class TelescopeSerializer(serializers.ModelSerializer):
    instrument_set = InstrumentSerializer(many=True, read_only=True)
    enclosure = serializers.HyperlinkedRelatedField(view_name='enclosure-detail', read_only=True)
    enclosure_id = serializers.IntegerField(write_only=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'lat', 'enclosure_id',
                  'long', 'enclosure', 'horizon', 'ha_limit_pos', 'ha_limit_neg', 'instrument_set', '__str__')
        model = Telescope


class EnclosureSerializer(serializers.ModelSerializer):
    telescope_set = TelescopeSerializer(many=True, read_only=True)
    site = serializers.HyperlinkedRelatedField(view_name='site-detail', read_only=True)
    site_id = serializers.IntegerField(write_only=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'site', 'site_id',
                  'telescope_set', '__str__')
        model = Enclosure


class SiteSerializer(serializers.ModelSerializer):
    enclosure_set = EnclosureSerializer(many=True, read_only=True)

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
