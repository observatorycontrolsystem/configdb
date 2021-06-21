from django.conf.urls import url, include
from django.views.generic.list import ListView
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework import permissions
from django.urls import path
from django.views.generic.base import TemplateView

from rest_framework.schemas.openapi import SchemaGenerator

from configdb.hardware import api_views
from .views import IndexView
from .models import Site, Telescope, Camera, Instrument, OpticalElementGroup, GenericModeGroup

router = routers.SimpleRouter()
router.register(r'sites', api_views.SiteViewSet)
router.register(r'enclosures', api_views.EnclosureViewSet)
router.register(r'telescopes', api_views.TelescopeViewSet)
router.register(r'instruments', api_views.InstrumentViewSet)
router.register(r'cameras', api_views.CameraViewSet)
router.register(r'cameratypes', api_views.CameraTypeViewSet)
router.register(r'instrumenttypes', api_views.InstrumentTypeViewSet)
router.register(r'opticalelementgroups', api_views.OpticalElementGroupViewSet)
router.register(r'opticalelements', api_views.OpticalElementViewSet)
router.register(r'genericmodegroups', api_views.GenericModeGroupViewSet)
router.register(r'genericmodes', api_views.GenericModeViewSet)


class ConfigDBSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema['info']['title'] = 'Configuration Database'
        schema['info']['description'] = 'An application with a database that stores observatory configuration'
        # Set the version to the latest git tag, and do not append any local information to the version number
        schema['info']['version'] = 'latest'
        return schema

schema_view = get_schema_view(
    permission_classes=[permissions.AllowAny,],
    generator_class=ConfigDBSchemaGenerator,
    public=True,
    authentication_classes=[]
    )


urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^html/sites/$', ListView.as_view(model=Site), name='html-site-list'),
    url(r'^html/telescopes/$', ListView.as_view(model=Telescope), name='html-telescope-list'),
    url(r'^html/cameras/$', ListView.as_view(model=Camera), name='html-camera-list'),
    url(r'^html/instruments/$', ListView.as_view(model=Instrument), name='html-instrument-list'),
    url(r'^html/opticalelementgroups/$', ListView.as_view(model=OpticalElementGroup), name='html-opticalelementgroup-list'),
    url(r'^html/genericmodegroups/$', ListView.as_view(model=GenericModeGroup), name='html-genericmodegroup-list'),
    url(r'^', include(router.urls)),
    path('openapi/', schema_view, name='openapi-schema'),
    path('redoc/', TemplateView.as_view(
        template_name='redoc.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='redoc')
]
