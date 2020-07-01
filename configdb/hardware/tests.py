import json

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from .models import Site, Instrument, Enclosure, Telescope, Camera, CameraType, InstrumentType
from .serializers import GenericModeSerializer


class SimpleHardwareTest(TestCase):
    def setUp(self):
        User.objects.create_user('tst_user', password='tst_pass')
        self.client = Client()

        self.site = mixer.blend(Site)
        self.enclosure = mixer.blend(Enclosure, site=self.site)
        self.telescope = mixer.blend(Telescope, enclosure=self.enclosure)

        self.camera_type = mixer.blend(CameraType)
        self.instrument_type = mixer.blend(InstrumentType)
        self.camera_type.save()
        self.camera = mixer.blend(Camera, camera_type=self.camera_type)
        self.instrument = mixer.blend(Instrument, science_camera=self.camera, autoguider_camera=self.camera,
                                      telescope=self.telescope, instrument_type=self.instrument_type, science_cameras=[self.camera])

    def test_homepage(self):
        response = self.client.get('/')
        self.assertContains(response, 'ConfigDB3', status_code=200)

    def test_write_site(self):
        site = {'name': 'Test Site', 'code': 'tst', 'active': True, 'timezone': -7, 'lat': 33.33, 'long': 22.22,
                'elevation': 1236, 'tz': 'US/Mountain', 'restart': '19:00:00'}
        self.client.login(username='tst_user', password='tst_pass')
        self.client.post('/sites/', site)

        saved_site = Site.objects.get(code=site['code'])
        self.assertEqual(saved_site.name, site['name'])

    def test_write_instrument(self):
        instrument = {
            'code': 'TST-INST-01', 'science_camera_id': self.camera.pk, 'state': 'DISABLED',
            'science_cameras_ids': [self.camera.pk], 'autoguider_camera_id': self.camera.pk,
            'telescope_id': self.telescope.pk, 'instrument_type_id': self.instrument_type.pk
        }
        self.client.login(username='tst_user', password='tst_pass')
        self.client.post('/instruments/', instrument)

        saved_instrument = Instrument.objects.get(code=instrument['code'])
        self.assertEqual(saved_instrument.science_camera.code, self.camera.code)
        self.assertEqual(saved_instrument.instrument_type.code, self.instrument_type.code)
        self.assertEqual(saved_instrument.telescope.code, self.telescope.code)


    def test_patch_instrument(self):
        self.assertEqual(self.instrument.state, Instrument.DISABLED)

        self.client.login(username='tst_user', password='tst_pass')
        self.client.patch('/instruments/{}/'.format(self.instrument.pk), json.dumps({'state': 'MANUAL'}),
                          content_type='application/json')
        self.instrument.refresh_from_db()
        self.assertEqual(self.instrument.state, Instrument.MANUAL)        

    def test_reject_invalid_cerberus_schema(self):
        bad_generic_mode_data = {'name': 'Readout Mode', 'overhead': 10.0, 'code': 'readout_mode_1', 'validation_schema': {'test': 'invalid'}}
        gms = GenericModeSerializer(data=bad_generic_mode_data)
        self.assertFalse(gms.is_valid())
        self.assertIn('SchemaError', gms.errors.get('validation_schema')[0])
