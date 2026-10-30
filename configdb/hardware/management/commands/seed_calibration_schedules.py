"""Seed the calibration windows and counts currently hardcoded in calibration_utils.

Covers BIAS, DARK, SKY_FLAT, STANDARD, the dusk AUTO_FOCUS, the routine
in-night AUTO_FOCUS and the FLOYDS standard, plus the sky flat filter order and
cadences and the target lists those draw on. Urgent autofocus is not seeded: it is
submitted by hand.

    python manage.py seed_calibration_schedules
"""
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from configdb.hardware.models import (
    CalibrationSchedule, CalibrationTarget, ConfigurationType, GenericMode, Instrument,
    InstrumentType, OpticalElement, Site, SkyFlatReadout, Telescope
)

# The Landolt and Stetson fields photometric standards are taken from, carried over
# from STD_FIELD in calibration_utils. Right ascension there is in hours and gets
# multiplied by 15 on the way out; these are already degrees.
#
# Seeded from STD_FIELD rather than from calibration-tom, which holds a more recently
# curated list but has never submitted an observation. This list is what produces the
# network's standards today. The difference is for operations to apply in the admin,
# which is the point of the targets being rows.
STANDARD_FIELDS = [
    ('L92', 13.839125, 0.764861111111),
    ('SA93', 28.7718, 0.76181),
    ('L94', 44.5887255, 1.18485833333333),
    ('L95', 58.2189165, -0.01496),
    ('SA95', 58.76535, 0.05742),
    ('RU149', 111.06405, -0.54664),
    ('SA101', 148.7166, -0.383),
    ('SA103', 179.2083, -0.45),
    ('L104', 190.545555, -0.543858333333333),
    ('L107', 235.02156, -0.33718),
    ('SA108', 249.34995, -0.5639),
    ('SA109', 266.18745, -0.417),
    ('L110', 280.599, 0.195),
    ('SA112', 310.755, 0.17),
    ('L113', 325.19745, 0.47642),
    ('SA114', 340.38, 0.17),
]

# Instrument types that take imaging calibrations. Spectrographs and autoguiders
# are excluded by having no row, which replaces the skip lists in the submitters.
# Bias, dark, sky flat and standard altitudes do not vary by instrument type, so a
# type listed here needs no per-type value. Retired types stay listed: their
# instruments are all DISABLED, which the effective endpoint skips, and a row is
# waiting if one comes back.
IMAGERS = ['1m0-SciCam-Sinistro', '0m4-SciCam-SBIG', '0m4-SciCam-QHY600', '0M4-SCICAM-FLI',
           '2m0-SciCam-Spectral', '2M0-SCICAM-MUSCAT', '1m0-SciCam-SBIG', '0m8-SciCam-SBIG']

# Dusk autofocus opens at a per-instrument-type altitude and always closes at -12.
# 0M4-SCICAM-FLI is absent: it has no value in calibration_utils to carry over, and
# all five of its instruments are MANUAL, so it takes no calibrations today anyway.
# QHY600 takes the 1m0 value because calibration_utils singles out only
# 0m4-SciCam-SBIG, so QHY600 falls through to -9.9.
FOCUS_START = {'0m4-SciCam-SBIG': -7.9, '0m4-SciCam-QHY600': -9.9,
               '2m0-SciCam-Spectral': -9.4, '2M0-SCICAM-MUSCAT': -9.4,
               '1m0-SciCam-Sinistro': -9.9, '1m0-SciCam-SBIG': -9.9, '0m8-SciCam-SBIG': -9.9}

# Bias and dark anchor on one solar altitude and extend by their own readout
# duration, so sun_alt_end stays blank. The 2m0 anchor is 7 rather than 6.
BIAS_DARK_ALT, BIAS_DARK_ALT_2M0 = 6, 7

# Sky flat order, from the master_filters sequence in calibration_type.py. Evening
# runs the list as written, morning reverses it. Only the codes present on a live
# imager are listed; the rest of that sequence names filters no current instrument
# carries. An element absent here keeps a null order and is never flat-fielded,
# which covers the pinholes and the opaque filter used for bias and dark.
SKY_FLAT_ORDER = ['CN', 'H-Alpha', 'SII', 'OIII', 'Y', 'U', 'up', 'zs', 'B', 'I', 'ip',
                  'V', 'R', 'rp', 'gp', 'Astrodon-Exo', 'w']

# Sky flat cadence per filter, from the tier sets in cadence/cadence.py. Every
# filter on a live imager falls in tier one or tier two, so three days and thirty
# are the only values in use.
SKY_FLAT_CADENCE_DAYS = {code: 30 if code in ('CN', 'OIII', 'SII') else 3
                         for code in SKY_FLAT_ORDER}

# Tier five gives everything read out in Sinistro's secondary mode a 45-day cadence.
# It never fires today, because the tier compares Readout objects by name and
# overhead while constructing them with blanks, so B, I, R, U and V fall through to
# the Days.MAX sentinel and take no flats at all while the rest get the three-day
# cadence of the primary mode. 45 is what the 2019 request asked for.
SECONDARY_READOUT_CADENCE_DAYS = {('1m0-SciCam-Sinistro', 'central_2k_2x2'): 45}

# Exposures per flat and how many filter and readout combinations one twilight
# covers. QHY600 packs in more because its electronic shutter and short readout
# allow a sub-second flat. MUSCAT takes one combination of narrowband positions.
FLAT_COUNTS = {'0m4-SciCam-QHY600': (5, 7), '2M0-SCICAM-MUSCAT': (6, 1)}
FLAT_COUNTS_DEFAULT = (5, 5)

FLOYDS = '2M0-FLOYDS-SCICAM'
# calibration_utils exposes every FLOYDS standard for 300 s, overriding the
# per-target times in floyds_standards.json. Seeded as deployed. A target that
# needs longer gets its own exposure_time in its config.
FLOYDS_SPECTRUM_EXPOSURE = 300


class Command(BaseCommand):
    help = 'Seed calibration schedules from the values hardcoded in calibration_utils'

    def add_arguments(self, parser):
        parser.add_argument('--floyds-standards', default='',
                            help='Path to floyds_standards.json, to seed the seasonal '
                                 'FLOYDS spectrophotometric standards')

    def handle(self, *args, **options):
        self.made = 0
        with transaction.atomic():
            for code, name in (('BIAS', 'Bias'), ('DARK', 'Dark'), ('SKY_FLAT', 'Sky Flat'),
                               ('STANDARD', 'Standard'), ('AUTO_FOCUS', 'Auto Focus'),
                               ('SPECTRUM', 'Spectrum')):
                ConfigurationType.objects.get_or_create(code=code, defaults={'name': name})
            self._bias_dark()
            self._sky_flats()
            self._sky_flat_filters()
            self._standards()
            self._dusk_focus()
            self._routine_focus()
            self._floyds_standard()
            self._standard_fields()
            self._floyds_standards(options['floyds_standards'])
        self.stdout.write(f'{self.made} rows written, {CalibrationSchedule.objects.count()} total')

    def _row(self, configuration_type, when, **kwargs):
        key = dict(configuration_type=ConfigurationType.objects.get(code=configuration_type),
                   instrument=kwargs.pop('instrument', None),
                   telescope=kwargs.pop('telescope', None),
                   instrument_type=kwargs.pop('instrument_type', None),
                   site=kwargs.pop('site', None),
                   when=when, direct_submission=kwargs.pop('direct_submission', True))
        _, created = CalibrationSchedule.objects.update_or_create(**key, defaults=kwargs)
        self.made += created

    @staticmethod
    def _types(codes):
        for code in codes:
            instrument_type = InstrumentType.objects.filter(code__iexact=code).first()
            if instrument_type:
                yield code, instrument_type

    def _bias_dark(self):
        for code, count in (('BIAS', 15), ('DARK', 5)):
            for _, instrument_type in self._types(IMAGERS):
                self._row(code, CalibrationSchedule.BOTH, instrument_type=instrument_type,
                          sun_alt_start=BIAS_DARK_ALT, exposures_per_run=count)

            # Both axes, because a telescope alone would also match the FLOYDS
            # instrument and the autoguiders sharing that telescope.
            for telescope in Telescope.objects.filter(code='2m0a'):
                for _, instrument_type in self._types(['2m0-SciCam-Spectral', '2M0-SCICAM-MUSCAT']):
                    if not Instrument.objects.filter(telescope=telescope,
                                                     instrument_type=instrument_type).exists():
                        continue
                    self._row(code, CalibrationSchedule.BOTH, telescope=telescope,
                              instrument_type=instrument_type, sun_alt_start=BIAS_DARK_ALT_2M0)

    def _sky_flats(self):
        for code, instrument_type in self._types(IMAGERS):
            exposures, elements = FLAT_COUNTS.get(code, FLAT_COUNTS_DEFAULT)
            dark_bound = -8 if 'MUSCAT' in code.upper() or 'SINISTRO' in code.upper() else -7
            self._row('SKY_FLAT', CalibrationSchedule.BOTH, instrument_type=instrument_type,
                      sun_alt_start=0, sun_alt_end=dark_bound,
                      exposures_per_run=exposures, elements_per_run=elements)

    def _sky_flat_filters(self):
        """The order and cadence the flat selection ranks filters by."""
        for order, code in enumerate(SKY_FLAT_ORDER, start=1):
            updated = OpticalElement.objects.filter(code=code).update(
                sky_flat_order=order, sky_flat_cadence_days=SKY_FLAT_CADENCE_DAYS[code])
            if not updated:
                self.stdout.write(f'no optical element {code}, skipped')

        for (type_code, mode_code), days in SECONDARY_READOUT_CADENCE_DAYS.items():
            instrument_type = InstrumentType.objects.filter(code__iexact=type_code).first()
            mode = instrument_type and GenericMode.objects.filter(
                code=mode_code, genericmodegroup__type='readout',
                genericmodegroup__instrument_type=instrument_type).first()
            if not mode:
                self.stdout.write(f'no {type_code} readout mode {mode_code}, skipped')
                continue
            _, created = SkyFlatReadout.objects.update_or_create(
                instrument_type=instrument_type, readout_mode=mode,
                defaults={'cadence_days': days})
            self.made += created

    def _standards(self):
        for code, instrument_type in self._types(IMAGERS):
            if 'MUSCAT' in code.upper():
                continue  # MUSCAT takes no standards, expressed by having no row
            self._row('STANDARD', CalibrationSchedule.MORNING, instrument_type=instrument_type,
                      sun_alt_start=-9, sun_alt_end=-12, exposures_per_run=2)

    def _dusk_focus(self):
        for code, instrument_type in self._types(FOCUS_START):
            self._row('AUTO_FOCUS', CalibrationSchedule.EVENING, instrument_type=instrument_type,
                      sun_alt_start=FOCUS_START[code], sun_alt_end=-12.0)

    def _routine_focus(self):
        """Queued autofocus offered in hourly windows from evening to morning -12.

        sor has always been skipped, so it gets a disabled row per type, which
        outranks the network row.
        """
        sor = Site.objects.filter(code='sor').first()
        for _, instrument_type in self._types(FOCUS_START):
            self._row('AUTO_FOCUS', CalibrationSchedule.EVENING, instrument_type=instrument_type,
                      direct_submission=False, sun_alt_start=-12.0, sun_alt_end=-12.0,
                      window_length_minutes=60)
            if sor:
                self._row('AUTO_FOCUS', CalibrationSchedule.EVENING, site=sor,
                          instrument_type=instrument_type, direct_submission=False, enabled=False)

    def _floyds_standard(self):
        """One queued spectrophotometric standard a night, any time between -12 twilights."""
        for _, instrument_type in self._types([FLOYDS]):
            self._row('SPECTRUM', CalibrationSchedule.EVENING, instrument_type=instrument_type,
                      direct_submission=False, sun_alt_start=-12.0, sun_alt_end=-12.0)

    def _standard_fields(self):
        """The imaging standard fields, available at any site all year."""
        standard = ConfigurationType.objects.get(code='STANDARD')
        for name, ra, dec in STANDARD_FIELDS:
            _, created = CalibrationTarget.objects.update_or_create(
                name=name, configuration_type=standard,
                defaults=dict(ra=ra, dec=dec, site=None, season_start='', season_end=''))
            self.made += created

    def _floyds_standards(self, path):
        """The seasonal spectrophotometric standards, one per site per date range.

        Each carries its own exposure time, slit and airmass limit, which vary by
        target, so they go in `config` rather than becoming columns.
        """
        if not path:
            self.stdout.write('  no --floyds-standards given, skipping FLOYDS targets')
            return
        with open(path) as f:
            by_site = json.load(f)

        spectrum = ConfigurationType.objects.get_or_create(
            code='SPECTRUM', defaults={'name': 'Spectrum'})[0]
        for site_code, entries in by_site.items():
            site = Site.objects.filter(code__iexact=site_code).first()
            if not site:
                self.stdout.write(f'  no site {site_code}, skipping its FLOYDS targets')
                continue
            for entry in entries:
                target = entry['config'].pop('target')
                entry['config']['instrument_configs']['exposure_time'] = FLOYDS_SPECTRUM_EXPOSURE
                _, created = CalibrationTarget.objects.update_or_create(
                    name=target['name'], configuration_type=spectrum, site=site,
                    season_start=entry['seasonal_start'], season_end=entry['seasonal_end'],
                    defaults=dict(
                        ra=target['ra'], dec=target['dec'],
                        proper_motion_ra=target.get('proper_motion_ra'),
                        proper_motion_dec=target.get('proper_motion_dec'),
                        config=entry['config']))
                self.made += created
