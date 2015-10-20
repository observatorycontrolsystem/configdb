from configdb3.hardware import api_views
from django.conf.urls import url, include
from .views import camera_mappings, IndexView
from rest_framework import routers
from django.views.generic.list import ListView
from .models import Site, Telescope, Camera, FilterWheel

router = routers.SimpleRouter()
router.register(r'sites', api_views.SiteViewSet)
router.register(r'enclosures', api_views.EnclosureViewSet)
router.register(r'telescopes', api_views.TelescopeViewSet)
router.register(r'instruments', api_views.InstrumentViewSet)
router.register(r'cameras', api_views.CameraViewSet)
router.register(r'cameratypes', api_views.CameraTypeViewSet)
router.register(r'mode', api_views.ModeViewSet)
router.register(r'filterwheels', api_views.FilterWheelViewSet)

urlpatterns = [
    url(r'^camera_mappings/', camera_mappings, name='camera-mappings'),
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^html/sites/$', ListView.as_view(model=Site), name='html-site-list'),
    url(r'^html/telescopes/$', ListView.as_view(model=Telescope), name='html-telescope-list'),
    url(r'^html/cameras/$', ListView.as_view(model=Camera), name='html-camera-list'),
    url(r'^html/filterwheels/$', ListView.as_view(model=FilterWheel), name='html-filterwheel-list'),
    url(r'^', include(router.urls))
]
