from rest_framework import viewsets, filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.schemas.openapi import AutoSchema

from configdb.hardware import serializers
from .models import (
    Site, Enclosure, Telescope, OpticalElementGroup, Instrument, Camera, OpticalElement,
    CameraType, GenericMode, GenericModeGroup, InstrumentType
)


class FilterableViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)


class SiteViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Sites'])
    queryset = Site.objects.all().prefetch_related(
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__optical_element_groups',
        'enclosure_set__telescope_set__instrument_set__autoguider_camera__optical_element_groups__optical_elements',
        'enclosure_set__telescope_set__instrument_set__science_cameras__optical_element_groups',
        'enclosure_set__telescope_set__instrument_set__science_cameras__optical_element_groups__optical_elements',
        'enclosure_set__telescope_set__instrument_set__instrument_type__mode_types',
        'enclosure_set__telescope_set__instrument_set__instrument_type__mode_types__modes',
    )
    serializer_class = serializers.SiteSerializer
    filter_fields = ('name', 'code')


class EnclosureViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Enclosures'])
    queryset = Enclosure.objects.all().select_related('site').prefetch_related(
        'telescope_set__instrument_set__autoguider_camera__optical_element_groups',
        'telescope_set__instrument_set__autoguider_camera__optical_element_groups__optical_elements',
        'telescope_set__instrument_set__science_cameras__optical_element_groups',
        'telescope_set__instrument_set__science_cameras__optical_element_groups__optical_elements',
        'telescope_set__instrument_set__instrument_type__mode_types',
        'telescope_set__instrument_set__instrument_type__mode_types__modes',
    )

    serializer_class = serializers.EnclosureSerializer
    filter_fields = ('name', 'code', 'site')


class TelescopeViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Telescopes'])
    queryset = Telescope.objects.all().select_related('enclosure__site').prefetch_related(
        'instrument_set__autoguider_camera__optical_element_groups',
        'instrument_set__autoguider_camera__optical_element_groups__optical_elements',
        'instrument_set__science_cameras__optical_element_groups',
        'instrument_set__science_cameras__optical_element_groups__optical_elements',
        'instrument_set__instrument_type__mode_types',
        'instrument_set__instrument_type__mode_types__modes',
    )
    serializer_class = serializers.TelescopeSerializer
    filter_fields = ('name', 'code', 'lat', 'long', 'horizon',
                     'enclosure')


class InstrumentFilter(django_filters.rest_framework.FilterSet):
    ''' Filter class used to specify a filterable attribute in the cameratype of science camera in this instrument.
        The added attribute to filter on is juse camera_type, which maps to the camera->camera_type->name parameter.
    '''
    camera_type = django_filters.CharFilter(field_name="science_cameras__camera_type__code")
    instrument_type = django_filters.CharFilter(field_name="instrument_type__code")
    telescope = django_filters.CharFilter(field_name="telescope__code")
    enclosure = django_filters.CharFilter(field_name="telescope__enclosure__code")
    site = django_filters.CharFilter(field_name="telescope__enclosure__site__code")
    state = django_filters.CharFilter(method='state_filter')

    class Meta:
        model = Instrument
        fields = ['telescope', 'science_cameras', 'autoguider_camera', 'instrument_type',
                  'camera_type', 'site', 'telescope', 'enclosure', 'state']

    def state_filter(self, queryset, name, value):
        ''' Allows us to do queries like ?state=MANUAL instead of ?state=10 '''
        print(name)
        for state in Instrument.STATE_CHOICES:
            if value.upper() == state[1]:
                return queryset.filter(state=state[0])
        return queryset


class InstrumentViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Instruments'])
    queryset = Instrument.objects.all().select_related('telescope__enclosure__site', 'instrument_type').prefetch_related(
        'autoguider_camera__optical_element_groups',
        'autoguider_camera__optical_element_groups__optical_elements',
        'science_cameras__optical_element_groups',
        'science_cameras__optical_element_groups__optical_elements',
        'instrument_type__mode_types',
        'instrument_type__mode_types__modes'
    ).distinct()
    serializer_class = serializers.InstrumentSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = InstrumentFilter


class CameraTypeViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Camera Types'])
    queryset = CameraType.objects.all()
    serializer_class = serializers.CameraTypeSerializer
    filter_fields = ('name', 'pscale')


class InstrumentTypeViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Instrument Types'])
    queryset = InstrumentType.objects.all()
    serializer_class = serializers.InstrumentTypeSerializer
    filter_fields = ('name', 'code', 'instrument_category')


class CameraViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Cameras'])
    queryset = Camera.objects.all().select_related('camera_type').prefetch_related(
        'optical_element_groups',
        'optical_element_groups__optical_elements'
    )
    serializer_class = serializers.CameraSerializer
    filter_fields = ('code', 'camera_type')


class OpticalElementGroupViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Optical Element Groups'])
    queryset = OpticalElementGroup.objects.all().prefetch_related('optical_elements').distinct()
    serializer_class = serializers.OpticalElementGroupSerializer
    filter_fields = ('name', 'type', 'optical_elements')


class OpticalElementViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Optical Elements'])
    queryset = OpticalElement.objects.all()
    serializer_class = serializers.OpticalElementSerializer
    filter_fields = ('id', 'name', 'code', 'schedulable')


class GenericModeGroupViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Generic Mode Groups'])
    queryset = GenericModeGroup.objects.all()
    serializer_class = serializers.GenericModeGroupSerializer


class GenericModeViewSet(FilterableViewSet):
    schema = AutoSchema(tags=['Generic Modes'])
    queryset = GenericMode.objects.all()
    serializer_class = serializers.GenericModeSerializer
    filter_fields = ('name', 'code', 'schedulable')
