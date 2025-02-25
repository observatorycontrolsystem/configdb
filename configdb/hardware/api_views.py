from rest_framework import viewsets, filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.schemas.openapi import AutoSchema

from configdb.hardware import serializers
from .models import (
    Site, Enclosure, Telescope, OpticalElementGroup, Instrument, Camera, OpticalElement,
    CameraType, GenericMode, GenericModeGroup, InstrumentType, ModeType, ConfigurationType,
    InstrumentCategory, ConfigurationTypeProperties
)


class CustomViewSchema(AutoSchema):
    """
    Class to generate OpenAPI schema from views
    """
    def get_filter_parameters(self, path, method):
        parameters = super().get_filter_parameters(path, method)
        # Infer the model from the view's queryset
        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        for parameter in parameters:
            # If the description matches the field name, then it isn't explicitly defined in the filter. Pull its description from the model's help text
            if parameter['description'] == parameter['name']:
                parameter['description'] = str(getattr(model, parameter['name']).field.help_text)
        return parameters


class FilterableViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)


class SiteViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Sites'])
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
    schema = CustomViewSchema(tags=['Enclosures'])
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
    schema = CustomViewSchema(tags=['Telescopes'])
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
                     'enclosure', 'aperture')


class InstrumentFilter(django_filters.rest_framework.FilterSet):
    ''' Filter class used to specify a filterable attribute in the cameratype of science camera in this instrument.
        The added attribute to filter on is juse camera_type, which maps to the camera->camera_type->name parameter.
    '''
    camera_type = django_filters.CharFilter(field_name="science_cameras__camera_type__code",
                                            label='Camera type code')
    instrument_type = django_filters.CharFilter(field_name="instrument_type__code",
                                                label='Instrument type code')
    telescope = django_filters.CharFilter(field_name="telescope__code",
                                          label='Telescope code')
    enclosure = django_filters.CharFilter(field_name="telescope__enclosure__code",
                                          label='Enclosure code')
    site = django_filters.CharFilter(field_name="telescope__enclosure__site__code",
                                     label='Site code')
    state = django_filters.MultipleChoiceFilter(choices=Instrument.STATE_CHOICES,
                                                label='Instrument state')

    class Meta:
        model = Instrument
        fields = ['telescope', 'science_cameras', 'autoguider_camera', 'instrument_type',
                  'camera_type', 'site', 'telescope', 'enclosure', 'state']


class InstrumentViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Instruments'])
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
    filterset_class = InstrumentFilter


class CameraTypeViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Camera Types'])
    queryset = CameraType.objects.all()
    serializer_class = serializers.CameraTypeSerializer
    filter_fields = ('name', 'pscale')


class InstrumentTypeViewSet(FilterableViewSet):
    custom_filter_annotations=[{'name': 'name', 'description': 'Camera type name'},
                               {'name': 'code', 'description': 'Instrument type code'},
                               {'name': 'instrument_category', 'description': 'Instrument category name'}]
    schema = CustomViewSchema(tags=['Instrument Types'])
    queryset = InstrumentType.objects.all()
    serializer_class = serializers.InstrumentTypeSerializer
    filter_fields = ('name', 'code', 'instrument_category')


class CameraViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Cameras'])
    queryset = Camera.objects.all().select_related('camera_type').prefetch_related(
        'optical_element_groups',
        'optical_element_groups__optical_elements'
    )
    serializer_class = serializers.CameraSerializer
    filter_fields = ('code', 'camera_type')


class OpticalElementGroupViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Optical Element Groups'])
    queryset = OpticalElementGroup.objects.all().prefetch_related('optical_elements').distinct()
    serializer_class = serializers.OpticalElementGroupSerializer
    filter_fields = ('name', 'type', 'optical_elements')


class OpticalElementViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Optical Elements'])
    queryset = OpticalElement.objects.all()
    serializer_class = serializers.OpticalElementSerializer
    filter_fields = ('id', 'name', 'code', 'schedulable')


class ModeTypeViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Mode Types'])
    queryset = ModeType.objects.all()
    serializer_class = serializers.ModeTypeSerializer


class InstrumentCategoryViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Instrument Category'])
    queryset = InstrumentCategory.objects.all()
    serializer_class = serializers.InstrumentCategorySerializer


class ConfigurationTypeViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Configuration Types'])
    queryset = ConfigurationType.objects.all()
    serializer_class = serializers.ConfigurationTypeSerializer


class ConfigurationTypePropertiesViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Configuration Type Properties'])
    queryset = ConfigurationTypeProperties.objects.all()
    serializer_class = serializers.ConfigurationTypePropertiesSerializer


class GenericModeGroupViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Generic Mode Groups'])
    queryset = GenericModeGroup.objects.all()
    serializer_class = serializers.GenericModeGroupSerializer


class GenericModeViewSet(FilterableViewSet):
    schema = CustomViewSchema(tags=['Generic Modes'])
    queryset = GenericMode.objects.all()
    serializer_class = serializers.GenericModeSerializer
    filter_fields = ('name', 'code', 'schedulable')
