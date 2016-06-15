from rest_framework import serializers
from .models import (Site, Enclosure, Telescope,
                     Instrument, Camera, Mode,
                     FilterWheel, CameraType, Filter)


class FilterWheelSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'filters', '__str__')
        model = FilterWheel
        depth = 1


class FilterSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'code', 'filter_type')
        model = Filter
        depth = 1


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'binning', 'overhead')
        model = Mode


class CameraTypeSerializer(serializers.ModelSerializer):
    default_mode = ModeSerializer()
    mode_set = ModeSerializer(many=True)

    class Meta:
        fields = ('id', 'size', 'pscale', 'default_mode', 'name', 'code', 'mode_set')
        model = CameraType


class CameraSerializer(serializers.ModelSerializer):
    camera_type = CameraTypeSerializer()
    instrument_set = serializers.HyperlinkedRelatedField(view_name='instrument-detail', read_only=True, many=True)
    autoguides_for = serializers.HyperlinkedRelatedField(view_name='instrument-detail', read_only=True, many=True)

    class Meta:
        fields = ('id', 'code', 'instrument_set','autoguides_for', 'camera_type', 'filter_wheel', 'filters')
        model = Camera


class InstrumentSerializer(serializers.ModelSerializer):
    science_camera = CameraSerializer()
    autoguider_camera = CameraSerializer()
    telescope = serializers.HyperlinkedRelatedField(view_name='telescope-detail', read_only=True)

    class Meta:
        fields = ('id', 'schedulable', 'telescope', 'science_camera',
                  'autoguider_camera', '__str__')
        model = Instrument


class TelescopeSerializer(serializers.ModelSerializer):
    instrument_set = InstrumentSerializer(many=True)
    enclosure = serializers.HyperlinkedRelatedField(view_name='enclosure-detail', read_only=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'lat',
                  'long', 'enclosure', 'horizon', 'ha_limit_pos', 'ha_limit_neg', 'instrument_set', '__str__')
        model = Telescope


class EnclosureSerializer(serializers.ModelSerializer):
    telescope_set = TelescopeSerializer(many=True)
    site = serializers.HyperlinkedRelatedField(view_name='site-detail', read_only=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'site',
                  'telescope_set', '__str__')
        model = Enclosure


class SiteSerializer(serializers.ModelSerializer):
    enclosure_set = EnclosureSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'timezone',
                  'elevation', 'enclosure_set', '__str__')
        model = Site
