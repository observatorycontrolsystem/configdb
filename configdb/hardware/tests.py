import json
from unittest.mock import patch

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from .models import (Site, Instrument, Enclosure, Telescope, Camera, CameraType, InstrumentType,
                     GenericMode, GenericModeGroup, ModeType, OpticalElement, OpticalElementGroup)
from .serializers import GenericModeSerializer


@patch('configdb.auth_backends.requests.post')
class TestOauth2Login(TestCase):
    def test_log_in(self, mock_post):
        mock_post.return_value.status_code = 200
        with self.settings(OAUTH_TOKEN_URL='localhost'):
            logged_in = self.client.login(username='bob', password='bobspass')
            self.assertTrue(logged_in)
            self.assertEqual(User.objects.filter(username='bob').count(), 1)

    def test_incorrect_login_credentials_fails(self, mock_post):
        mock_post.return_value.status_code = 403
        with self.settings(OAUTH_TOKEN_URL='localhost'):
            logged_in = self.client.login(username='bob', password='notbobspass')
            self.assertFalse(logged_in)
            self.assertEqual(User.objects.filter(username='bob').count(), 0)

    def test_log_in_with_no_oauth_url_set_fails(self, mock_post):
        with self.settings(OAUTH_TOKEN_URL=''):
            logged_in = self.client.login(username='bob', password='bobspass')
            self.assertFalse(logged_in)
            self.assertEqual(User.objects.filter(username='bob').count(), 0)


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
        self.instrument = mixer.blend(Instrument, autoguider_camera=self.camera, telescope=self.telescope,
                                      instrument_type=self.instrument_type, science_cameras=[self.camera])

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
            'code': 'TST-INST-01', 'state': 'DISABLED',
            'science_cameras_ids': [self.camera.pk], 'autoguider_camera_id': self.camera.pk,
            'telescope_id': self.telescope.pk, 'instrument_type_id': self.instrument_type.pk
        }
        self.client.login(username='tst_user', password='tst_pass')
        self.client.post('/instruments/', instrument)

        saved_instrument = Instrument.objects.get(code=instrument['code'])
        self.assertEqual(saved_instrument.science_cameras.all()[0].code, self.camera.code)
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

    def test_mode_group_str(self):
        mode_type = mixer.blend(ModeType, id='type1')
        self.assertEqual(str(mode_type), 'type1')
        mode1 = mixer.blend(GenericMode, code='mode1', name='MyMode')
        mode2 = mixer.blend(GenericMode, code='mode2')
        self.assertEqual(str(mode1), 'mode1: MyMode')
        mode_group = mixer.blend(GenericModeGroup, type=mode_type, modes=[mode1, mode2])
        self.assertEqual(str(mode_group), 'mode1,mode2')

    def test_optical_elements_str(self):
        oe1 = mixer.blend(OpticalElement, code='oe1')
        oe2 = mixer.blend(OpticalElement, code='oe2')
        self.assertEqual(str(oe1), 'oe1')
        oeg = mixer.blend(OpticalElementGroup, type='oeg_type', name='oeg_name', optical_elements=[oe1, oe2])
        self.assertEqual(str(oeg), 'oeg_name - oeg_type: oe1,oe2')
