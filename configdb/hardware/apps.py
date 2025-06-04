from django.apps import AppConfig
from django.conf import settings


def can_submit_to_heroic():
    return settings.HEROIC_API_URL and settings.HEROIC_API_TOKEN and settings.HEROIC_OBSERVATORY


class HardwareConfig(AppConfig):
    name = 'configdb.hardware'
    
    def ready(self):
        # Only load the heroic communication signals if heroic settings are set
        if can_submit_to_heroic():
            import configdb.hardware.signals.handlers  # noqa
        super().ready()
