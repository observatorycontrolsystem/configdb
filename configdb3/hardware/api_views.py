from rest_framework import viewsets, filters
from configdb3.hardware import serializers
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (Site, Enclosure, Telescope,
                     Instrument, Camera, Mode,
                     FilterWheel, CameraType, Filter)


class FilterableViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)


class SiteViewSet(FilterableViewSet):
    queryset = Site.objects.all().prefetch_related(
        'enclosure_set__telescope_set__instrument_set__science_camera__camera_type__mode_set'
    ).prefetch_related(
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__camera_type__mode_set'
    ).prefetch_related(
        'enclosure_set__telescope_set__instrument_set__science_camera__camera_type__default_mode'
    ).prefetch_related(
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__camera_type__default_mode'
    ).prefetch_related(
        'enclosure_set__telescope_set__instrument_set__science_camera__filter_wheel__filters'
    ).prefetch_related(
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__filter_wheel__filters'
    )
    serializer_class = serializers.SiteSerializer
    filter_fields = ('name', 'code')


class EnclosureViewSet(FilterableViewSet):
    queryset = Enclosure.objects.all().select_related('site').prefetch_related(
        'telescope_set__instrument_set__science_camera__camera_type__mode_set',
        'telescope_set__instrument_set__autoguider_camera__camera_type__mode_set',
        'telescope_set__instrument_set__science_camera__camera_type__default_mode',
        'telescope_set__instrument_set__autoguider_camera__camera_type__default_mode',
        'telescope_set__instrument_set__science_camera__filter_wheel__filters',
        'telescope_set__instrument_set__autoguider_camera__filter_wheel__filters'
    )

    serializer_class = serializers.EnclosureSerializer
    filter_fields = ('name', 'code', 'site')


class TelescopeViewSet(FilterableViewSet):
    queryset = Telescope.objects.all().select_related('enclosure__site').prefetch_related(
        'instrument_set__science_camera__camera_type__mode_set',
        'instrument_set__autoguider_camera__camera_type__mode_set',
        'instrument_set__science_camera__camera_type__default_mode',
        'instrument_set__autoguider_camera__camera_type__default_mode',
        'instrument_set__science_camera__filter_wheel__filters',
        'instrument_set__autoguider_camera__filter_wheel__filters'

    )
    serializer_class = serializers.TelescopeSerializer
    filter_fields = ('name', 'code', 'lat', 'long', 'horizon',
                     'enclosure')


class InstrumentFilter(django_filters.rest_framework.FilterSet):
    ''' Filter class used to specify a filterable attribute in the cameratype of science camera in this instrument.
        The added attribute to filter on is juse camera_type, which maps to the camera->camera_type->name parameter.
    '''
    camera_type = django_filters.CharFilter(field_name="science_camera__camera_type__code")
    telescope = django_filters.CharFilter(field_name="telescope__code")
    enclosure = django_filters.CharFilter(field_name="telescope__enclosure__code")
    site = django_filters.CharFilter(field_name="telescope__enclosure__site__code")
    state = django_filters.CharFilter(method='state_filter')

    class Meta:
        model = Instrument
        fields = ['telescope', 'science_camera', 'autoguider_camera',
                  'camera_type', 'site', 'telescope', 'enclosure', 'state']

    def state_filter(self, queryset, name, value):
        ''' Allows us to do queries like ?state=ENABLED instead of ?state=10 '''
        print(name)
        for state in Instrument.STATE_CHOICES:
            if value.upper() == state[1]:
                return queryset.filter(state=state[0])
        return queryset


class InstrumentViewSet(FilterableViewSet):
    queryset = Instrument.objects.all().select_related('telescope__enclosure__site').prefetch_related(
        'science_camera__camera_type__mode_set',
        'autoguider_camera__camera_type__mode_set',
        'science_camera__camera_type__default_mode',
        'autoguider_camera__camera_type__default_mode',
        'science_camera__filter_wheel__filters',
        'autoguider_camera__filter_wheel__filters'
    ).distinct()
    serializer_class = serializers.InstrumentSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = InstrumentFilter


class CameraTypeViewSet(FilterableViewSet):
    queryset = CameraType.objects.all()
    serializer_class = serializers.CameraTypeSerializer
    filter_fields = ('name', 'pscale')


class CameraViewSet(FilterableViewSet):
    queryset = Camera.objects.all().select_related('camera_type').prefetch_related(
        'camera_type__mode_set',
        'camera_type__default_mode',
        'filter_wheel__filters',
    )
    serializer_class = serializers.CameraSerializer
    filter_fields = ('code', 'filter_wheel', 'camera_type')


class ModeViewSet(FilterableViewSet):
    queryset = Mode.objects.all()
    serializer_class = serializers.ModeSerializer
    filter_fields = ('binning', 'overhead', 'camera_type')


class FilterWheelFilter(django_filters.rest_framework.FilterSet):
    ''' Filter class used to specify a filterable attribute in the cameratype of cameras that use this filterwheel.
        The added attribute to filter on is juse camera_type, which maps to the camera->camera_type->name parameter.
    '''
    camera_type = django_filters.CharFilter(field_name="camera__camera_type__code")

    class Meta:
        model = FilterWheel
        fields = ['filters', 'id', 'camera_type']


class FilterWheelViewSet(FilterableViewSet):
    queryset = FilterWheel.objects.all().prefetch_related('filters').distinct()
    serializer_class = serializers.FilterWheelSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = FilterWheelFilter


class FilterViewSet(FilterableViewSet):
    queryset = Filter.objects.all()
    serializer_class = serializers.FilterSerializer
    filter_fields = ('id', 'name', 'code', 'filter_type')
