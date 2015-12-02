from django.core.management.base import BaseCommand, CommandError
import requests
from configdb3.hardware.models import *
from os import getenv


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
    if not 'results' in json_results:
        raise Exception()
    return json_results['results']


class Command(BaseCommand):

    def handle(self, *args, **options):

        # load in the filters first
        camera_filters = get_model_data('filters')
        for camera_filter in camera_filters:
            filter, created = Filter.objects.get_or_create(
                name=camera_filter['name'],
                code=camera_filter['code'],
                filter_type=camera_filter['filter_type']
            )
            if created:
                print('created: ', filter)

        # then create the filter wheels, which use a manyToMany field of filters
        filter_wheels = get_model_data('filterwheels')
        # must delete the filterwheels first, as we are recreating them all
        FilterWheel.objects.all().delete()
        for filter_wheel in filter_wheels:
            f_wheel = FilterWheel.objects.create()
            for camera_filter in filter_wheel['filters']:
                filter = Filter.objects.get(
                    name=camera_filter['name'],
                    code=camera_filter['code'],
                    filter_type=camera_filter['filter_type']
                )
                f_wheel.filters.add(filter)
            f_wheel.save()
            print("created: ", f_wheel)

        # then loop through the cameras, creating the camera_types, modes, and finally the cameras
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
            for camera_mode in camera_type['mode_set']:
                mode, created = Mode.objects.get_or_create(
                    binning=camera_mode['binning'],
                    overhead=camera_mode['overhead'],
                    camera_type=ctype
                )
                if created:
                    print('created: ', mode)
            mode = Mode.objects.get(
                    binning=camera_type['default_mode']['binning'],
                    overhead=camera_type['default_mode']['overhead'],
                    camera_type=ctype
            )
            ctype.default_mode = mode
            ctype.save()

            for filter_wheel in FilterWheel.objects.all():
                filter_wheel_filter_set = set()
                for f in str(filter_wheel).split(','):
                    filter_wheel_filter_set.add(f)
                camera_filter_set = set()
                for f in camera['filters'].split(','):
                    camera_filter_set.add(f)
                if filter_wheel_filter_set == camera_filter_set:
                    cam, created = Camera.objects.get_or_create(
                        code=camera['code'],
                        camera_type=ctype,
                        filter_wheel=filter_wheel
                    )
                    if created:
                        print("created: ", cam)
                    break

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