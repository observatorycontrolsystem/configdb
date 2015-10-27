from rest_framework import serializers
from .models import (Site, Enclosure, Telescope,
                     Instrument, Camera, Mode,
                     FilterWheel, CameraType)


class FilterWheelSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'filters')
        model = FilterWheel
        depth = 1


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'binning', 'overhead')
        model = Mode


class CameraTypeSerializer(serializers.ModelSerializer):
    default_mode = ModeSerializer()
    mode_set = ModeSerializer(many=True)

    class Meta:
        fields = ('id', 'size', 'pscale', 'default_mode', 'name', 'mode_set')
        model = CameraType


class CameraSerializer(serializers.ModelSerializer):
    camera_type = CameraTypeSerializer()

    class Meta:
        fields = ('id', 'code', 'camera_type', 'filter_wheel', 'filters')
        model = Camera


class InstrumentSerializer(serializers.ModelSerializer):
    science_camera = CameraSerializer()
    autoguider_camera = CameraSerializer()

    class Meta:
        fields = ('id', 'telescope', 'science_camera',
                  'autoguider_camera')
        model = Instrument


class TelescopeSerializer(serializers.ModelSerializer):
    instrument_set = InstrumentSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'lat',
                  'long', 'enclosure', 'instrument_set')
        model = Telescope


class EnclosureSerializer(serializers.ModelSerializer):
    telescope_set = TelescopeSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'site',
                  'telescope_set')
        model = Enclosure


class SiteSerializer(serializers.ModelSerializer):
    enclosure_set = EnclosureSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'code', 'active', 'timezone',
                  'enclosure_set')
        model = Site
