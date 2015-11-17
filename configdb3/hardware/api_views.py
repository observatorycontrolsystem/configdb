from rest_framework import viewsets, filters
from configdb3.hardware import serializers
import django_filters
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


class InstrumentFilter(django_filters.FilterSet):
    ''' Filter class used to specify a filterable attribute in the cameratype of science camera in this instrument.
        The added attribute to filter on is juse camera_type, which maps to the camera->camera_type->name parameter.
    '''
    camera_type = django_filters.CharFilter(name="science_camera__camera_type__code")
    telescope = django_filters.CharFilter(name="telescope__code")
    enclosure = django_filters.CharFilter(name="telescope__enclosure__code")
    site = django_filters.CharFilter(name="telescope__enclosure__site__code")

    class Meta:
        model = Instrument
        fields = ['telescope', 'science_camera', 'autoguider_camera',
                  'camera_type', 'site', 'telescope', 'enclosure', 'active']


class InstrumentViewSet(FilterableViewSet):
    queryset = Instrument.objects.all().distinct()
    serializer_class = serializers.InstrumentSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = InstrumentFilter


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


class FilterWheelFilter(django_filters.FilterSet):
    ''' Filter class used to specify a filterable attribute in the cameratype of cameras that use this filterwheel.
        The added attribute to filter on is juse camera_type, which maps to the camera->camera_type->name parameter.
    '''
    camera_type = django_filters.CharFilter(name="camera__camera_type__code")

    class Meta:
        model = FilterWheel
        fields = ['filters', 'id', 'camera_type']


class FilterWheelViewSet(FilterableViewSet):
    queryset = FilterWheel.objects.all().distinct()
    serializer_class = serializers.FilterWheelSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = FilterWheelFilter
