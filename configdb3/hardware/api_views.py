from rest_framework import viewsets, filters
from configdb3.hardware import serializers
from .models import (Site, Enclosure, Telescope,
                     Instrument, Camera, Mode,
                     FilterWheel, CameraType)


class FilterableViewSet(viewsets.ModelViewSet):
    filter_backends = (filters.DjangoFilterBackend,)


class SiteViewSet(FilterableViewSet):
    queryset = Site.objects.all()
    serializer_class = serializers.SiteSerializer
    filter_fields = ('name', 'code', 'active')


class EnclosureViewSet(FilterableViewSet):
    queryset = Enclosure.objects.all()
    serializer_class = serializers.EnclosureSerializer
    filter_fields = ('name', 'code', 'site')


class TelescopeViewSet(FilterableViewSet):
    queryset = Telescope.objects.all()
    serializer_class = serializers.TelescopeSerializer
    filter_fields = ('name', 'code', 'active', 'lat', 'long',
                     'enclosure')


class InstrumentViewSet(FilterableViewSet):
    queryset = Instrument.objects.all()
    serializer_class = serializers.InstrumentSerializer
    filter_fields = ('telescope', 'science_camera', 'autoguider_camera')


class CameraTypeViewSet(FilterableViewSet):
    queryset = CameraType.objects.all()
    serializer_class = serializers.CameraTypeSerializer
    filter_fields = ('name', 'pscale')


class CameraViewSet(FilterableViewSet):
    queryset = Camera.objects.all()
    serializer_class = serializers.CameraSerializer
    filter_fields = ('code', 'filter_wheel', 'camera_type')


class ModeViewSet(FilterableViewSet):
    queryset = Mode.objects.all()
    serializer_class = serializers.ModeSerializer
    filter_fields = ('binning', 'overhead', 'camera_type')


class FilterWheelViewSet(FilterableViewSet):
    queryset = FilterWheel.objects.all()
    serializer_class = serializers.FilterWheelSerializer
    filter_fields = ('filters',)
