import json
from http import HTTPStatus
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from .models import (Site, Instrument, Enclosure, Telescope, Camera, CameraType, InstrumentType,
                     GenericMode, GenericModeGroup, ModeType, OpticalElement, OpticalElementGroup)
from .serializers import GenericModeSerializer, InstrumentTypeSerializer


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

    def test_write_instrument_type(self):
        good_instrument_type = {'name': 'Instrument Type', 'code': 'inst1'}
        self.client.login(username='tst_user', password='tst_pass')
        result = self.client.post('/instrumenttypes/', good_instrument_type)
        self.assertEqual(result.status_code, 201)
        saved_instrument_type = InstrumentType.objects.get(code=good_instrument_type['code'])
        self.assertEqual(saved_instrument_type.name, good_instrument_type['name'])

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

    def test_patch_instrument_invalid_state_fails(self):
        self.assertEqual(self.instrument.state, Instrument.DISABLED)

        self.client.login(username='tst_user', password='tst_pass')
        response = self.client.patch('/instruments/{}/'.format(self.instrument.pk), json.dumps({'state': 'UNWELL'}),
                                     content_type='application/json')
        self.instrument.refresh_from_db()
        self.assertEqual(self.instrument.state, Instrument.DISABLED)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_or_instrument_states(self):
        new_instrument = mixer.blend(Instrument, autoguider_camera=self.camera, telescope=self.telescope,
                                     instrument_type=self.instrument_type, science_cameras=[self.camera],
                                     state=Instrument.SCHEDULABLE)

        
        response = self.client.get('/instruments/', data={'state': ['DISABLED', 'SCHEDULABLE']}, content_type='application/x-www-form-urlencoded')
        self.assertEqual(len(response.json()['results']), 2)

        response = self.client.get('/instruments/', data={'state': 'DISABLED'}, content_type='application/x-www-form-urlencoded')
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(str(new_instrument), response.json()['results'][0]['__str__'])

        response = self.client.get('/instruments/', data={'state': 'SCHEDULABLE'}, content_type='application/x-www-form-urlencoded')
        self.assertEqual(len(response.json()['results']), 1)

        response = self.client.get('/instruments/', data={'state': 'MANUAL'}, content_type='application/x-www-form-urlencoded')
        self.assertEqual(len(response.json()['results']), 0)

    def test_reject_invalid_cerberus_schema_generic_mode(self):
        bad_generic_mode_data = {'name': 'Readout Mode', 'overhead': 10.0, 'code': 'readout_mode_1', 'validation_schema': {'test': 'invalid'}}
        gms = GenericModeSerializer(data=bad_generic_mode_data)
        self.assertFalse(gms.is_valid())
        self.assertIn('SchemaError', gms.errors.get('validation_schema')[0])

    def test_reject_invalid_cerberus_schema_instrument_type(self):
        bad_instrument_type = {'name': 'Instrument Type', 'code': 'inst1', 'validation_schema': {'test': 'invalid'}}
        its = InstrumentTypeSerializer(data=bad_instrument_type)
        self.assertFalse(its.is_valid())
        self.assertIn('SchemaError', its.errors.get('validation_schema')[0])

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
