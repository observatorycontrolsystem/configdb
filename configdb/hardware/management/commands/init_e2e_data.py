import logging
import sys

from django.core.management.base import BaseCommand

from configdb.hardware.models import (
    Site, Enclosure, Telescope, Instrument, Camera, CameraType, GenericMode, GenericModeGroup,
    OpticalElement, OpticalElementGroup, ModeType, InstrumentType
)

logger = logging.getLogger()


FILTERS = ['r', 'g', 'b', 'air']


class Command(BaseCommand):
    help = 'Creates basic structures in configdb for e2e tests'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--site', type=str, default='cit',
                            help='Site code to use')
        parser.add_argument('--latitude', required=True, type=float,
                            help='Site latitude in degrees')
        parser.add_argument('--longitude', required=True, type=float,
                            help='Site longitude in degrees')

    def add_telescope(self, site, longitude, latitude, obs, tel, ins):

        site, _ = Site.objects.get_or_create(code=site, defaults={'elevation': 0, 'timezone': 0})
        site.lat = latitude
        site.long = longitude
        site.elevation = 0
        site.active = True
        site.timezone = 0
        site.save()

        enclosure, _ = Enclosure.objects.get_or_create(code=obs, site=site)
        enclosure.active = True
        enclosure.save()

        telescope, _ = Telescope.objects.get_or_create(code=tel, enclosure=enclosure,
                                                       defaults={'lat': latitude, 'long': longitude, 'horizon': 15,
                                                                 'ha_limit_pos': 4.6, 'ha_limit_neg': -4.6})

        camera_type, _ = CameraType.objects.get_or_create(name='1M0-SCICAM-SINISTRO', code='1M0-SCICAM-SINISTRO',
                                                       defaults={'pscale': 0, 'size': '0x0'})
        camera_type.save()

        instrument_type, _ = InstrumentType.objects.get_or_create(name='1M0-SCICAM-SINISTRO', code='1M0-SCICAM-SINISTRO')
        instrument_type.configuration_types = ['EXPOSE', 'BIAS', 'DARK', 'AUTO_FOCUS', 'SCRIPT', 'STANDARD']
        instrument_type.save()

        # Now set up the modes for the instrument_type
        readout_mode_type, _ = ModeType.objects.get_or_create(id='readout')
        readout_mode, _ = GenericMode.objects.get_or_create(code='default',
            defaults={'name': 'Sinistro Readout Mode', 'overhead': 0,
                      'validation_schema': {"binning": {"type": "integer", "allowed": [1], "default": 1}}}
        )
        readout_mode_group, _ = GenericModeGroup.objects.get_or_create(instrument_type=instrument_type, type=readout_mode_type,
                                                                       default=readout_mode)
        readout_mode_group.modes.add(readout_mode)
        readout_mode_group.save()

        # Now set up the camera
        camera, _ = Camera.objects.get_or_create(code='xx04', camera_type=camera_type)

        # Set the optical elements
        optical_element_group, _ = OpticalElementGroup.objects.get_or_create(name='Test Filter', type='filters')
        for filter_code in FILTERS:
            optical_element, _ = OpticalElement.objects.get_or_create(code=filter_code, defaults={'name': filter_code})
            optical_element_group.optical_elements.add(optical_element)
            optical_element_group.default = optical_element
        optical_element_group.save()
        camera.optical_element_groups.add(optical_element_group)
        camera.save()

        instrument, _ = Instrument.objects.get_or_create(code=ins, telescope=telescope, autoguider_camera=camera, 
                                                         instrument_type=instrument_type)
        instrument.science_cameras.add(camera)
        instrument.state = Instrument.MANUAL
        instrument.save()

    def handle(self, *args, **options):
        longitude = options['longitude']
        latitude = options['latitude']
        site_str = options['site']
        self.add_telescope(site=site_str, longitude=longitude, latitude=latitude, obs="doma", tel="1m0a", ins="xx04")
        self.add_telescope(site=site_str, longitude=longitude, latitude=latitude, obs="clma", tel="2m0a", ins="xx05")
        
        sys.exit(0)
