"""Load a configdb `sites/` API payload into this database.

Seeds a development or test instance from a dump taken off a running configdb:

    curl https://configdb.example/sites/?format=json > sites.json
    python manage.py load_sites_payload sites.json

Tolerant of schema drift. A dump taken before camera types were split out of
instrument types still loads, with anything missing left at the model default.
Objects are matched on their natural keys and updated, so re-running is safe.
Generic modes and optical element groups have no natural key of their own, since
codes and names repeat with different settings, so they are matched within the
instrument type or camera that holds them.
"""
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from configdb.hardware.models import (
    Site, Enclosure, Telescope, Instrument, Camera, CameraType, GenericMode, GenericModeGroup,
    OpticalElement, OpticalElementGroup, ModeType, InstrumentType, ConfigurationType,
    ConfigurationTypeProperties
)


class Command(BaseCommand):
    help = 'Load a configdb sites/ payload into this database'

    def add_arguments(self, parser):
        parser.add_argument('payload', help='Path to a sites/ API response in JSON')
        parser.add_argument('--sites', default='', help='Comma separated site codes, default all')

    def handle(self, *args, **options):
        with open(options['payload']) as f:
            payload = json.load(f)
        results = payload['results'] if 'results' in payload else payload
        wanted = {c.strip().lower() for c in options['sites'].split(',') if c.strip()}

        self.counts = {}
        with transaction.atomic():
            for site in results:
                if wanted and site['code'].lower() not in wanted:
                    continue
                self._site(site)

        for name in sorted(self.counts):
            self.stdout.write(f'  {name}: {self.counts[name]}')

    def _made(self, name, created):
        if created:
            self.counts[name] = self.counts.get(name, 0) + 1

    # -- hierarchy ---------------------------------------------------------

    def _site(self, blob):
        site, created = Site.objects.update_or_create(
            code=blob['code'],
            defaults=self._fields(blob, ('name', 'active', 'lat', 'long', 'elevation', 'timezone', 'tz')),
        )
        self._made('sites', created)
        for enclosure in blob.get('enclosure_set', []):
            self._enclosure(site, enclosure)

    def _enclosure(self, site, blob):
        enclosure, created = Enclosure.objects.update_or_create(
            site=site, code=blob['code'],
            defaults=self._fields(blob, ('name', 'active')),
        )
        self._made('enclosures', created)
        for telescope in blob.get('telescope_set', []):
            self._telescope(enclosure, telescope)

    def _telescope(self, enclosure, blob):
        telescope, created = Telescope.objects.update_or_create(
            enclosure=enclosure, code=blob['code'],
            defaults=self._fields(blob, (
                'name', 'active', 'serial_number', 'lat', 'long', 'horizon', 'aperture',
                'ha_limit_neg', 'ha_limit_pos', 'slew_rate', 'minimum_slew_overhead',
                'instrument_change_overhead', 'telescope_front_padding', 'zenith_blind_spot')),
        )
        self._made('telescopes', created)
        for instrument in blob.get('instrument_set', []):
            self._instrument(telescope, instrument)

    def _instrument(self, telescope, blob):
        instrument_type = self._instrument_type(blob['instrument_type'])
        science = [self._camera(c) for c in blob.get('science_cameras', [])]
        autoguider = self._camera(blob['autoguider_camera']) if blob.get('autoguider_camera') else None
        if autoguider is None:
            # The model requires one. Reuse the science camera rather than skip the
            # instrument, which would lose it from the hierarchy entirely.
            autoguider = science[0] if science else None
        if autoguider is None:
            return

        instrument, created = Instrument.objects.update_or_create(
            telescope=telescope, code=blob['code'],
            defaults={'instrument_type': instrument_type, 'autoguider_camera': autoguider,
                      **self._fields(blob, ('state',))},
        )
        self._made('instruments', created)
        instrument.science_cameras.set(science)

    def _instrument_type(self, blob):
        instrument_type, created = InstrumentType.objects.update_or_create(
            code=blob['code'],
            defaults=self._fields(blob, (
                'name', 'fixed_overhead_per_exposure', 'observation_front_padding',
                'config_front_padding', 'acquire_exposure_time',
                'default_acceptability_threshold', 'allow_self_guiding')),
        )
        self._made('instrument types', created)

        for entry in blob.get('configuration_types', []):
            configuration_type, _ = ConfigurationType.objects.get_or_create(
                code=entry['code'], defaults={'name': entry.get('name', entry['code'])})
            ConfigurationTypeProperties.objects.update_or_create(
                instrument_type=instrument_type, configuration_type=configuration_type,
                defaults=self._fields(entry, ('config_change_overhead',)))

        for group in blob.get('mode_types', []):
            self._mode_group(instrument_type, group)
        return instrument_type

    def _mode_group(self, instrument_type, blob):
        mode_type, _ = ModeType.objects.get_or_create(id=blob['type'])
        modes = []
        for mode in blob.get('modes', []):
            existing = GenericMode.objects.filter(
                code=mode['code'], genericmodegroup__instrument_type=instrument_type,
                genericmodegroup__type=mode_type).first()
            modes.append(self._save('modes', existing or GenericMode(code=mode['code']),
                                    self._fields(mode, ('name', 'overhead', 'validation_schema'))))

        default = next((m for m in modes if m.code == blob.get('default')), None)
        group, _ = GenericModeGroup.objects.update_or_create(
            instrument_type=instrument_type, type=mode_type, defaults={'default': default})
        group.modes.set(modes)

    def _camera(self, blob):
        camera_type = self._camera_type(blob.get('camera_type') or {'code': 'unknown', 'name': 'unknown'})
        camera, created = Camera.objects.update_or_create(
            code=blob['code'],
            defaults={'camera_type': camera_type, **self._fields(blob, ('orientation', 'host'))},
        )
        self._made('cameras', created)
        camera.optical_element_groups.set(
            [self._optical_element_group(camera, g) for g in blob.get('optical_element_groups', [])])
        return camera

    def _camera_type(self, blob):
        name = blob.get('name') or blob['code']
        # pscale has no model default, so a dump without one needs a placeholder.
        existing = CameraType.objects.filter(name=name).first()
        return self._save('camera types', existing or CameraType(name=name, pscale=0.0),
                          self._fields(blob, ('code', 'size', 'pscale', 'pixels_x', 'pixels_y', 'max_rois')))

    def _optical_element_group(self, camera, blob):
        elements = []
        for element in blob.get('optical_elements', []):
            optical_element, created = OpticalElement.objects.update_or_create(
                code=element['code'],
                defaults=self._fields(element, ('name', 'schedulable')))
            self._made('optical elements', created)
            elements.append(optical_element)

        default = next((e for e in elements if e.code == blob.get('default')), None)
        existing = camera.optical_element_groups.filter(name=blob['name'], type=blob['type']).first()
        group = self._save('optical element groups',
                           existing or OpticalElementGroup(name=blob['name'], type=blob['type']),
                           {'default': default, **self._fields(blob, ('element_change_overhead',))})
        group.optical_elements.set(elements)
        return group

    def _save(self, name, obj, fields):
        created = obj.pk is None
        for field, value in fields.items():
            setattr(obj, field, value)
        obj.save()
        self._made(name, created)
        return obj

    @staticmethod
    def _fields(blob, names):
        """Only the keys this dump actually carries, so an older schema still loads."""
        return {n: blob[n] for n in names if blob.get(n) is not None}
