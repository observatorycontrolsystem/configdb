import logging
import sys

from django.core.management.base import BaseCommand

from configdb.hardware.models import (
    Site, Enclosure, Telescope, Instrument, Camera, CameraType, GenericMode, GenericModeGroup,
    OpticalElement, OpticalElementGroup, ModeType, InstrumentType, InstrumentCategory, ConfigurationType
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
        parser.add_argument('--instrument-state', dest='instrument_state', type=str, default='MANUAL',
                            help='Instrument State to use (defaults to MANUAL)')

    def add_configuration_types(self, instrument_type):
        expose_config_type, _ = ConfigurationType.objects.get_or_create(code='EXPOSE', name='Expose', schedulable=True)
        autofocus_config_type, _ = ConfigurationType.objects.get_or_create(code='AUTO_FOCUS', name='Auto Focus', schedulable=True)
        standard_config_type, _ = ConfigurationType.objects.get_or_create(code='STANDARD', name='Standard', schedulable=True)
        script_config_type, _ = ConfigurationType.objects.get_or_create(code='SCRIPT', name='Script', schedulable=True)
        bias_config_type, _ = ConfigurationType.objects.get_or_create(code='BIAS', name='Bias', schedulable=False)
        dark_config_type, _ = ConfigurationType.objects.get_or_create(code='DARK', name='Dark', schedulable=False)
        instrument_type.configuration_types.add(expose_config_type)
        instrument_type.configuration_types.add(autofocus_config_type)
        instrument_type.configuration_types.add(standard_config_type)
        instrument_type.configuration_types.add(script_config_type)
        instrument_type.configuration_types.add(bias_config_type)
        instrument_type.configuration_types.add(dark_config_type)
        instrument_type.save()

    def add_telescope(self, site, longitude, latitude, obs, tel, ins, ins_state):

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

        imager_category, _ = InstrumentCategory.objects.get_or_create(code='IMAGE')
        InstrumentCategory.objects.get_or_create(code='SPECTRO')

        instrument_type, _ = InstrumentType.objects.get_or_create(name='1M0-SCICAM-SINISTRO', code='1M0-SCICAM-SINISTRO',
                                                                  instrument_category=imager_category)
        self.add_configuration_types(instrument_type)

        # Now set up the modes for the instrument_type
        readout_mode_type, _ = ModeType.objects.get_or_create(id='readout')
        readout_mode, _ = GenericMode.objects.get_or_create(code='default',
            defaults={'name': 'Sinistro Readout Mode', 'overhead': 0,
                      'validation_schema': {"bin_x": {"type": "integer", "allowed": [1], "default": 1},
                                            "bin_y": {"type": "integer", "allowed": [1], "default": 1}}
                     }
        )

        readout_mode_group, _ = GenericModeGroup.objects.get_or_create(instrument_type=instrument_type, type=readout_mode_type,
                                                                       default=readout_mode)
        readout_mode_group.modes.add(readout_mode)
        readout_mode_group.save()

        guide_mode_type, _ = ModeType.objects.get_or_create(id='guiding')
        guide_mode_off, _ = GenericMode.objects.get_or_create(code='OFF',
            defaults={'name': 'Guide OFF', 'overhead': 0, 'validation_schema': {}}
        )
        guide_mode_on, _ = GenericMode.objects.get_or_create(code='ON',
            defaults={'name': 'Guide ON', 'overhead': 5, 'validation_schema': {}}
        )
        guide_mode_group, _ = GenericModeGroup.objects.get_or_create(instrument_type=instrument_type, type=guide_mode_type,
                                                                       default=guide_mode_off)
        guide_mode_group.modes.add(guide_mode_off)
        guide_mode_group.modes.add(guide_mode_on)
        guide_mode_group.save()

        acquire_mode_type, _ = ModeType.objects.get_or_create(id='acquisition')
        acquire_mode_off, _ = GenericMode.objects.get_or_create(code='OFF',
            defaults={'name': 'Acquire OFF', 'overhead': 0, 'validation_schema': {}}
        )
        acquire_mode_group, _ = GenericModeGroup.objects.get_or_create(instrument_type=instrument_type, type=acquire_mode_type,
                                                                       default=acquire_mode_off)
        acquire_mode_group.modes.add(acquire_mode_off)
        acquire_mode_group.save()

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
        instrument.state = ins_state
        instrument.save()

    def handle(self, *args, **options):
        if options['instrument_state'] not in dict(Instrument.STATE_CHOICES).values():
            logger.warning(f"Invalid instrument state {options['instrument_state']}.")
            sys.exit(1)
        else:
            for key, val in dict(Instrument.STATE_CHOICES).items():
                if options['instrument_state'] == val:
                    ins_state = key
                    break

        longitude = options['longitude']
        latitude = options['latitude']
        site_str = options['site']
        self.add_telescope(site=site_str, longitude=longitude, latitude=latitude, obs="doma", tel="1m0a", ins="xx04", ins_state=ins_state)
        self.add_telescope(site=site_str, longitude=longitude, latitude=latitude, obs="clma", tel="2m0a", ins="xx05", ins_state=ins_state)

        sys.exit(0)
