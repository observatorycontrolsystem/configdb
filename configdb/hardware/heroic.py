from django.conf import settings
from urllib.parse import urljoin
import requests
import logging

from configdb.hardware.models import Instrument, Telescope, Site
from configdb.hardware.apps import can_submit_to_heroic


logger = logging.getLogger()


def instrument_status_conversion(state: str):
    ''' Converts instrument state to HEROIC instrument status
    '''
    if state == 'DISABLED' or state == 'MANUAL':
        return 'UNAVAILABLE'
    elif state == 'SCHEDULABLE':
        return 'SCHEDULABLE'
    else:
        return 'AVAILABLE'


def telescope_status_conversion(telescope: Telescope):
    return 'SCHEDULABLE' if telescope.active and telescope.enclosure.active and telescope.enclosure.site.active else 'UNAVAILABLE'


def heroic_site_id(site: Site):
    ''' Extract a HEROIC id for the site.
        This concatenates the observatory.site for human readability
    '''
    return f"{settings.HEROIC_OBSERVATORY}.{site.code}"


def heroic_telescope_id(telescope: Telescope):
    ''' Extract a HEROIC id for the telescope
        This concatenates the observatory.site.telescope for human readability
    '''
    return f"{heroic_site_id(telescope.enclosure.site)}.{telescope.enclosure.code}-{telescope.code}"


def heroic_instrument_id(instrument: Instrument):
    ''' Extract a HEROIC id for the instrument
        This concatenates the observatory.site.telescope.instrument
        for human-readability.
    '''
    return f"{heroic_telescope_id(instrument.telescope)}.{instrument.code}"


def heroic_optical_element_groups(instrument: Instrument):
    ''' Puts the optical element groups of an instrument in the format for reporting to HEROIC
    '''
    optical_element_groups = {}
    for camera in instrument.science_cameras.all():
        for optical_element_group in camera.optical_element_groups.all():
            optical_element_groups[optical_element_group.type] = {'options': []}
            if optical_element_group.default:
                optical_element_groups[optical_element_group.type]['default'] = optical_element_group.default.code
            for optical_element in optical_element_group.optical_elements.all():
                optical_element_groups[optical_element_group.type]['options'].append({
                    'id': optical_element.code,
                    'name': optical_element.name,
                    'schedulable': optical_element.schedulable
                })
    return optical_element_groups


def heroic_operation_modes(instrument: Instrument):
    ''' Puts the generic mode groups of an instrument in the format for reporting to HEROIC
    '''
    operation_modes = {}
    for generic_mode_group in instrument.instrument_type.mode_types.all():
        operation_modes[generic_mode_group.type.id] = {'options': []}
        if generic_mode_group.default:
            operation_modes[generic_mode_group.type.id]['default'] = generic_mode_group.default.code
        for mode in generic_mode_group.modes.all():
            operation_modes[generic_mode_group.type.id]['options'].append({
                'id': mode.code,
                'name': mode.name,
                'schedulable': mode.schedulable
            })
    return operation_modes


def instrument_to_heroic_instrument_capabilities(instrument: Instrument):
    ''' Extracts the current instrument capabilities of an instrument to send to HEROIC
    '''
    capabilities = {
        'instrument': heroic_instrument_id(instrument),
        'status': instrument_status_conversion(instrument.state),
        'optical_element_groups': heroic_optical_element_groups(instrument),
        'operation_modes': heroic_operation_modes(instrument)
    }
    return capabilities


def telescope_to_heroic_telescope_properties(telescope: Telescope):
    ''' Extracts the current telescope properties of a telescope to send to HEROIC
    '''
    telescope_payload = {
        'name': f"{telescope.name} - {telescope.enclosure.name}",
        'site': heroic_site_id(telescope.enclosure.site),
        'aperture': telescope.aperture,
        'latitude': telescope.lat,
        'longitude': telescope.long,
        'horizon': telescope.horizon,
        'negative_ha_limit': telescope.ha_limit_neg,
        'positive_ha_limit': telescope.ha_limit_pos,
        'zenith_blind_spot': telescope.zenith_blind_spot
    }
    return telescope_payload


def send_to_heroic(api_endpoint: str, payload: dict, update: bool = False):
    ''' Function to send data to HEROIC API endpoints
    '''
    headers = {'Authorization': f'Token {settings.HEROIC_API_TOKEN}'}
    url = urljoin(settings.HEROIC_API_URL, api_endpoint)
    if update:
        response = requests.patch(url, headers=headers, json=payload)
    else:
        response = requests.post(url, headers=headers, json=payload)
    logger.warning(response.json())
    response.raise_for_status()



def create_heroic_instrument(instrument: Instrument):
    ''' Create a new instrument payload and send it to HEROIC
    '''
    if (instrument.telescope.enclosure.site.code not in settings.HEROIC_EXCLUDE_SITES and str(instrument.telescope) not in settings.HEROIC_EXCLUDE_TELESCOPES):
        instrument_payload = {
            'id': heroic_instrument_id(instrument),
            'name': f"{instrument.instrument_type.name} - {instrument.code}",
            'telescope': heroic_telescope_id(instrument.telescope),
            'available': True
        }
        try:
            send_to_heroic('instruments/', instrument_payload)
        except Exception as e:
            logger.error(f'Failed to create heroic instrument {str(instrument)}: {repr(e)}')


def update_heroic_instrument_capabilities(instrument: Instrument):
    ''' Send the current instrument capabilities of an instrument to HEROIC
        if it is not DISABLED and heroic is set up in settings.py
    '''
    if can_submit_to_heroic() and instrument.state != 'DISABLED' and instrument.telescope.enclosure.site.code not in settings.HEROIC_EXCLUDE_SITES and str(instrument.telescope) not in settings.HEROIC_EXCLUDE_TELESCOPES:
        capabilities = instrument_to_heroic_instrument_capabilities(instrument)
        try:
            send_to_heroic('instrument-capabilities/', capabilities)
        except Exception as e:
            logger.error(f'Failed to create heroic instrument {str(instrument)} capability update: {repr(e)}')


def create_heroic_telescope(telescope: Telescope):
    ''' Create a new telescope payload and send it to HEROIC
    '''
    if telescope.enclosure.site.code not in settings.HEROIC_EXCLUDE_SITES and str(telescope) not in settings.HEROIC_EXCLUDE_TELESCOPES:
        telescope_payload = telescope_to_heroic_telescope_properties(telescope)
        telescope_payload['id'] = heroic_telescope_id(telescope)
        telescope_payload['status'] = telescope_status_conversion(telescope)
        if telescope_payload['status'] != 'SCHEDULABLE':
            telescope_payload['reason'] = 'Telescope is currently marked as inactive to prevent usage'
        try:
            send_to_heroic('telescopes/', telescope_payload)
        except Exception as e:
            logger.error(f'Failed to create heroic telescope {str(telescope)}: {repr(e)}')


def update_heroic_telescope_properties(telescope: Telescope):
    ''' Send updated telescope properties to HEROIC when they change
    '''
    if telescope.enclosure.site.code not in settings.HEROIC_EXCLUDE_SITES and str(telescope) not in settings.HEROIC_EXCLUDE_TELESCOPES:
        telescope_update_payload = telescope_to_heroic_telescope_properties(telescope)
        try:
            send_to_heroic(f'telescopes/{heroic_telescope_id(telescope)}/', telescope_update_payload, update=True)
        except Exception as e:
            logger.error(f'Failed to update heroic telescope {str(telescope)}: {repr(e)}')


def site_to_heroic_site_properties(site: Site):
    ''' Extracts the current site properties of a site to send to HEROIC
    '''
    site_payload = {
        'name': site.name,
        'observatory': settings.HEROIC_OBSERVATORY,
        'elevation': site.elevation,
        'timezone': site.tz
    }
    return site_payload


def create_heroic_site(site: Site):
    ''' Create a new site payload and send it to HEROIC
    '''
    if site.code not in settings.HEROIC_EXCLUDE_SITES:
        site_payload = site_to_heroic_site_properties(site)
        site_payload['id'] = heroic_site_id(site)
        try:
            send_to_heroic('sites/', site_payload)
        except Exception as e:
            logger.error(f'Failed to create heroic site {str(site)}: {repr(e)}')


def update_heroic_site(site: Site):
    ''' Send updated site properties to HEROIC when they change
    '''
    if site.code not in settings.HEROIC_EXCLUDE_SITES:
        site_payload = site_to_heroic_site_properties(site)
        try:
            send_to_heroic(f'sites/{heroic_site_id(site)}/', site_payload, update=True)
        except Exception as e:
            logger.error(f'Failed to update heroic site {str(site)}: {repr(e)}')
