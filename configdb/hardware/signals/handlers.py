''' These signals right now are only used for when HEROIC details are set in the settings
    They are used to propagate model information to the HEROIC service
'''
from django.dispatch import receiver
from django.db.models.signals import pre_save

from configdb.hardware.models import Instrument, Telescope, Site

import configdb.hardware.heroic as heroic


@receiver(pre_save, sender=Instrument)
def on_save_instrument(sender, instance, *args, **kwargs):
    if not instance.pk:
        heroic.create_heroic_instrument(instance)


@receiver(pre_save, sender=Telescope)
def on_save_telescope(sender, instance, *args, **kwargs):
    # Telescope save triggers updates to its properties or its creation to heroic
    if instance.pk:
        heroic.update_heroic_telescope_properties(instance)
    else:
        heroic.create_heroic_telescope(instance)


@receiver(pre_save, sender=Site)
def on_save_site(sender, instance, *args, **kwargs):
    # Site save triggers updates to its properties or its creation to heroic
    if instance.pk:
        heroic.update_heroic_site(instance)
    else:
        heroic.create_heroic_site(instance)
