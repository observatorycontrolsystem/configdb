from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.views.generic.base import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework import permissions

from .hardware import urls as hardware_urls
from .schema import ConfigDBSchemaGenerator

schema_view = get_schema_view(
    permission_classes=[permissions.AllowAny,],
    generator_class=ConfigDBSchemaGenerator,
    public=True,
    authentication_classes=[]
    )

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(hardware_urls)),
    path('openapi/', schema_view, name='openapi-schema'),
    path('redoc/', TemplateView.as_view(
        template_name='redoc.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='redoc')
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
