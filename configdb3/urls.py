from django.conf.urls import include, url
from django.contrib import admin
from .hardware import urls as hardware_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(hardware_urls))
]
