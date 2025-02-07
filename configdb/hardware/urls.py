from django.urls import re_path, include
from django.views.generic.list import ListView
from rest_framework import routers

from configdb.hardware import api_views
from .views import IndexView
from .models import Site, Telescope, Camera, Instrument, OpticalElementGroup, GenericModeGroup

import ocs_authentication.auth_profile.urls as authprofile_urls


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
router.register(r'modetypes', api_views.ModeTypeViewSet)
router.register(r'configurationtypes', api_views.ConfigurationTypeViewSet)
router.register(r'configurationtypeproperties', api_views.ConfigurationTypePropertiesViewSet)
router.register(r'instrumentcategories', api_views.InstrumentCategoryViewSet)

urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name='index'),
    re_path(r'^authprofile/', include(authprofile_urls)),
    re_path(r'^html/sites/$', ListView.as_view(model=Site), name='html-site-list'),
    re_path(r'^html/telescopes/$', ListView.as_view(model=Telescope), name='html-telescope-list'),
    re_path(r'^html/cameras/$', ListView.as_view(model=Camera), name='html-camera-list'),
    re_path(r'^html/instruments/$', ListView.as_view(model=Instrument), name='html-instrument-list'),
    re_path(r'^html/opticalelementgroups/$', ListView.as_view(model=OpticalElementGroup), name='html-opticalelementgroup-list'),
    re_path(r'^html/genericmodegroups/$', ListView.as_view(model=GenericModeGroup), name='html-genericmodegroup-list'),
    re_path(r'^', include(router.urls))
]
