from os import getenv

import requests
from django.core.management.base import BaseCommand

from configdb3.hardware.models import Site, Enclosure, Telescope, Instrument, Camera, CameraType


CONFIGDB_URL = getenv('CONFIGDB_URL', 'http://172.16.5.173:8000/')


def get_model_data(model_type):
    '''
        Function calls the configdb endpoint to get the list of filters and their attributes. Dogpile.cache is
        used to cache the dictionary decoded response. This is necessary because json decoding time is large.
    :return: json list of filter details
    '''
    try:
        r = requests.get(CONFIGDB_URL + model_type + '/')
    except requests.exceptions.RequestException as e:
        msg = "{}".format(e.__class__.__name__)
        raise Exception(msg)
    r.encoding = 'UTF-8'
    if not r.status_code == 200:
        raise Exception()
    json_results = r.json()
    if 'results' not in json_results:
        raise Exception()
    return json_results['results']


class Command(BaseCommand):

    def handle(self, *args, **options):
        # TODO: Create optical elements and modes

        # Loop through the cameras, creating the camera_types, modes, and finally the cameras
        cameras = get_model_data('cameras')
        for camera in cameras:
            camera_type = camera['camera_type']
            ctype, created = CameraType.objects.get_or_create(
                name=camera_type['name'],
                code=camera_type['code'],
                size=camera_type['size'],
                pscale=camera_type['pscale']
            )
            if created:
                print('created: ', ctype)

            cam, created = Camera.objects.get_or_create(
                code=camera['code'],
                camera_type=ctype,
            )
            if created:
                print("created: ", cam)

        # now go through the sites and create the sites, enclosures, telescopes, and instruments
        sites = get_model_data('sites')
        for site in sites:
            s, created = Site.objects.get_or_create(
                name=site['name'],
                code=site['code'],
                active=site['active'],
                timezone=site['timezone']
            )
            if created:
                print("created: ", s)

            for enclosure in site['enclosure_set']:
                enc, created = Enclosure.objects.get_or_create(
                    name=enclosure['name'],
                    code=enclosure['code'],
                    active=enclosure['active'],
                    site=s
                )
                if created:
                    print("created: ", enc)

                for telescope in enclosure['telescope_set']:
                    tel, created = Telescope.objects.get_or_create(
                        name=telescope['name'],
                        code=telescope['code'],
                        active=telescope['active'],
                        lat=telescope['lat'],
                        long=telescope['long'],
                        enclosure=enc
                    )
                    if created:
                        print("created: ", tel)

                    for instrument in telescope['instrument_set']:
                        print("science camera: ", instrument['science_camera']['code'])
                        science_cam = Camera.objects.get(
                            code=instrument['science_camera']['code']
                        )
                        print("autoguider camera: ", instrument['autoguider_camera']['code'])
                        autoguider_cam = Camera.objects.get(
                            code=instrument['autoguider_camera']['code']
                        )
                        inst, created = Instrument.objects.get_or_create(
                            schedulable=instrument['schedulable'],
                            telescope=tel,
                            science_camera=science_cam,
                            autoguider_camera=autoguider_cam,
                            autoguider_type=instrument['autoguider_type']
                        )
                        if created:
                            print("created: ", inst)
