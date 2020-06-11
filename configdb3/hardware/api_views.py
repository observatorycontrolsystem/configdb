from rest_framework import viewsets, filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from configdb3.hardware import serializers
from .models import (
    Site, Enclosure, Telescope, OpticalElementGroup, Instrument, Camera, OpticalElement,
    CameraType, GenericMode, GenericModeGroup
)


class FilterableViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)


class SiteViewSet(FilterableViewSet):
    queryset = Site.objects.all().prefetch_related(
        'enclosure_set__telescope_set__instrument_set__science_camera__camera_type__mode_types',
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__camera_type__mode_types',
        'enclosure_set__telescope_set__instrument_set__science_camera__camera_type__mode_types__modes',
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__camera_type__mode_types__modes',
        'enclosure_set__telescope_set__instrument_set__science_camera__optical_element_groups',
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__optical_element_groups',
        'enclosure_set__telescope_set__instrument_set__science_camera__optical_element_groups__optical_elements',
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__optical_element_groups__optical_elements',
    )
    serializer_class = serializers.SiteSerializer
    filter_fields = ('name', 'code')


class EnclosureViewSet(FilterableViewSet):
    queryset = Enclosure.objects.all().select_related('site').prefetch_related(
        'telescope_set__instrument_set__science_camera__camera_type__mode_types',
        'telescope_set__instrument_set__autoguider_camera__camera_type__mode_types',
        'telescope_set__instrument_set__science_camera__camera_type__mode_types__modes',
        'telescope_set__instrument_set__autoguider_camera__camera_type__mode_types__modes',
        'telescope_set__instrument_set__science_camera__optical_element_groups',
        'telescope_set__instrument_set__autoguider_camera__optical_element_groups',
        'telescope_set__instrument_set__science_camera__optical_element_groups__optical_elements',
        'telescope_set__instrument_set__autoguider_camera__optical_element_groups__optical_elements',
    )

    serializer_class = serializers.EnclosureSerializer
    filter_fields = ('name', 'code', 'site')


class TelescopeViewSet(FilterableViewSet):
    queryset = Telescope.objects.all().select_related('enclosure__site').prefetch_related(
        'instrument_set__science_camera__camera_type__mode_types',
        'instrument_set__autoguider_camera__camera_type__mode_types',
        'instrument_set__science_camera__camera_type__mode_types__modes',
        'instrument_set__autoguider_camera__camera_type__mode_types__modes',
        'instrument_set__science_camera__optical_element_groups',
        'instrument_set__autoguider_camera__optical_element_groups',
        'instrument_set__science_camera__optical_element_groups__optical_elements',
        'instrument_set__autoguider_camera__optical_element_groups__optical_elements',
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
        ''' Allows us to do queries like ?state=MANUAL instead of ?state=10 '''
        print(name)
        for state in Instrument.STATE_CHOICES:
            if value.upper() == state[1]:
                return queryset.filter(state=state[0])
        return queryset


class InstrumentViewSet(FilterableViewSet):
    queryset = Instrument.objects.all().select_related('telescope__enclosure__site').prefetch_related(
        'science_camera__camera_type__mode_types',
        'autoguider_camera__camera_type__mode_types',
        'science_camera__camera_type__mode_types__modes',
        'autoguider_camera__camera_type__mode_types__modes',
        'science_camera__optical_element_groups',
        'autoguider_camera__optical_element_groups',
        'science_camera__optical_element_groups__optical_elements',
        'autoguider_camera__optical_element_groups__optical_elements',
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
        'camera_type__mode_types',
        'camera_type__mode_types__modes',
        'optical_element_groups',
        'optical_element_groups__optical_elements'
    )
    serializer_class = serializers.CameraSerializer
    filter_fields = ('code', 'camera_type')


class OpticalElementGroupViewSet(FilterableViewSet):
    queryset = OpticalElementGroup.objects.all().prefetch_related('optical_elements').distinct()
    serializer_class = serializers.OpticalElementGroupSerializer
    filter_fields = ('name', 'type', 'optical_elements')


class OpticalElementViewSet(FilterableViewSet):
    queryset = OpticalElement.objects.all()
    serializer_class = serializers.OpticalElementSerializer
    filter_fields = ('id', 'name', 'code', 'schedulable')


class GenericModeGroupViewSet(FilterableViewSet):
    queryset = GenericModeGroup.objects.all()
    serializer_class = serializers.GenericModeGroupSerializer


class GenericModeViewSet(FilterableViewSet):
    queryset = GenericMode.objects.all()
    serializer_class = serializers.GenericModeSerializer
