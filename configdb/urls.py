from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .hardware import urls as hardware_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(hardware_urls))
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
