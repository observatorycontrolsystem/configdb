from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from .models import Site, Instrument, Enclosure, Telescope, Camera, CameraType, Filter, FilterWheel, Mode
from mixer.backend.django import mixer
import json


class SimpleHardwareTest(TestCase):
    def setUp(self):
        User.objects.create_user('tst_user', password='tst_pass')
        self.client = Client()

        self.site = mixer.blend(Site)
        self.enclosure = mixer.blend(Enclosure, site=self.site)
        self.telescope = mixer.blend(Telescope, enclosure=self.enclosure)

        self.filter1 = mixer.blend(Filter)
        self.filterwheel = mixer.blend(FilterWheel, filters=[self.filter1, ])
        self.camera_type = mixer.blend(CameraType)
        self.mode = mixer.blend(Mode, camera_type=self.camera_type)
        self.camera_type.default_mode = self.mode
        self.camera_type.save()
        self.camera = mixer.blend(Camera, camera_type=self.camera_type, filter_wheel=self.filterwheel)
        self.instrument = mixer.blend(Instrument, science_camera=self.camera, autoguider_camera=self.camera,
                                      telescope=self.telescope)

    def test_homepage(self):
        response = self.client.get('/')
        self.assertContains(response, 'ConfigDB3', status_code=200)

    def test_write_site(self):
        site = {'name': 'Test Site', 'code': 'tst', 'active': True, 'timezone': -7, 'lat': 33.33, 'long': 22.22,
                'elevation': 1236, 'tz': 'US/Mountain', 'restart': '19:00:00'}
        self.client.login(username='tst_user', password='tst_pass')
        self.client.post('/sites/', site)

        saved_site = Site.objects.get(code='tst')
        self.assertEqual(saved_site.name, site['name'])

    def test_patch_instrument(self):
        self.assertEqual(self.instrument.state, Instrument.DISABLED)

        self.client.login(username='tst_user', password='tst_pass')
        self.client.patch('/instruments/{}/'.format(self.instrument.pk), json.dumps({'state': 'ENABLED'}),
                          content_type='application/json')
        self.instrument.refresh_from_db()
        self.assertEqual(self.instrument.state, Instrument.ENABLED)
