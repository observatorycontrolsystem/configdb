import json
import reversion
import time_machine
from datetime import datetime
from http import HTTPStatus
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from .models import (Site, Instrument, Enclosure, Telescope, Camera, CameraType, InstrumentType,
                     GenericMode, GenericModeGroup, ModeType, OpticalElement, OpticalElementGroup)
from .serializers import GenericModeSerializer, InstrumentTypeSerializer


class BaseHardwareTest(TestCase):
    def setUp(self):
        User.objects.create_user('tst_user', password='tst_pass')
        self.client = Client()

        self.site = mixer.blend(Site, code='tst')
        self.enclosure = mixer.blend(Enclosure, site=self.site, code='doma')
        self.telescope = mixer.blend(Telescope, enclosure=self.enclosure, code='1m0a', active=True)
        self.camera_type = mixer.blend(CameraType)
        self.instrument_type = mixer.blend(InstrumentType)
        self.camera_type.save()
        self.camera = mixer.blend(Camera, camera_type=self.camera_type)
        self.instrument = mixer.blend(Instrument, autoguider_camera=self.camera, telescope=self.telescope,
                                      instrument_type=self.instrument_type, science_cameras=[self.camera],
                                      state=Instrument.SCHEDULABLE, code='myInst01')


class SimpleHardwareTest(BaseHardwareTest):
    def setUp(self):
        super().setUp()
        # Set instrument to initially be disabled
        self.instrument.state = Instrument.DISABLED
        self.instrument.save()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertContains(response, 'ConfigDB3', status_code=200)

    def test_write_site(self):
        site = {'name': 'Test Site', 'code': 'tss', 'active': True, 'timezone': -7, 'lat': 33.33, 'long': 22.22,
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
        self.assertEqual(str(self.instrument), response.json()['results'][0]['__str__'])

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


class TestAvailabilityHistory(BaseHardwareTest):
    def setUp(self):
        super().setUp()
        # Now setup the initial reversion Versions for the availability history test
        with time_machine.travel("2023-01-01 00:00:00"):
            with reversion.create_revision():
                self.instrument.save()
            with reversion.create_revision():
                self.telescope.save()

    def _update_instrument_revision(self, instrument, state, modified):
        with time_machine.travel(modified):
            with reversion.create_revision():
                instrument.state = state
                instrument.save()

    def _update_telescope_revision(self, telescope, active, modified):
        with time_machine.travel(modified):
            with reversion.create_revision():
                telescope.active = active
                telescope.save()

    def test_requires_instrument_or_telescope_defined(self):
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?telescope_id={self.telescope.code}&site_id={self.site.code}')
        self.assertContains(response, 'Must supply either instrument_id or site_id, enclosure_id, and telescope_id in params', status_code=400)

    def test_requires_instrument_to_exist(self):
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?instrument_id=FakeInst')
        self.assertContains(response, 'No instrument found with code FakeInst', status_code=404)

    def test_requires_telescope_to_exist(self):
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?telescope_id=FakeCode&site_id={self.site.code}&enclosure_id={self.enclosure.code}')
        self.assertContains(response, f'No telescope found with code {self.site.code}.{self.enclosure.code}.FakeCode', status_code=404)

    def test_requires_date_params_be_parseable(self):
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?instrument_id={self.instrument.code}&start=notadate')
        self.assertContains(response, f'The format used for the start/end parameters is not parseable', status_code=400)

    def test_instrument_availability_history(self):
        self._update_instrument_revision(self.instrument, Instrument.MANUAL, "2023-02-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.SCHEDULABLE, "2023-03-01 00:00:00")
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?instrument_id={self.instrument.code}')
        expected_intervals = {'availability_intervals': [
            {'start': datetime(2023, 3, 1).isoformat(), 'end': datetime(2024, 1, 1).isoformat()},
            {'start': datetime(2023, 1, 1).isoformat(), 'end': datetime(2023, 2, 1).isoformat()}]}
        self.assertEqual(response.json(), expected_intervals)

    def test_instrument_availability_history_caps_start(self):
        self._update_instrument_revision(self.instrument, Instrument.MANUAL, "2023-02-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.SCHEDULABLE, "2023-03-01 00:00:00")
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?instrument_id={self.instrument.code}&start=2023-04-01')
        expected_intervals = {'availability_intervals': [
            {'start': datetime(2023, 3, 1).isoformat(), 'end': datetime(2024, 1, 1).isoformat()}]}
        self.assertEqual(response.json(), expected_intervals)

    def test_instrument_availability_history_caps_start_end(self):
        self._update_instrument_revision(self.instrument, Instrument.MANUAL, "2023-02-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.SCHEDULABLE, "2023-03-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.MANUAL, "2023-04-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.SCHEDULABLE, "2023-05-01 00:00:00")
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?instrument_id={self.instrument.code}&start=2023-03-10&end=2023-04-10')
        expected_intervals = {'availability_intervals': [
            {'start': datetime(2023, 3, 1).isoformat(), 'end': datetime(2023, 4, 1).isoformat()}]}
        self.assertEqual(response.json(), expected_intervals)

    def test_telescope_availability_history(self):
        self._update_telescope_revision(self.telescope, False, "2023-02-10 00:00:00")
        self._update_telescope_revision(self.telescope, True, "2023-03-10 00:00:00")

        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?telescope_id={self.telescope.code}&site_id={self.site.code}&enclosure_id={self.enclosure.code}')
        expected_intervals = {'availability_intervals': [
            {'start': datetime(2023, 3, 10).isoformat(), 'end': datetime(2024, 1, 1).isoformat()},
            {'start': datetime(2023, 1, 1).isoformat(), 'end': datetime(2023, 2, 10).isoformat()}]}
        self.assertEqual(response.json(), expected_intervals)

    def test_telescope_and_instrument_availability_history(self):
        self._update_instrument_revision(self.instrument, Instrument.MANUAL, "2023-02-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.SCHEDULABLE, "2023-03-01 00:00:00")
        self._update_telescope_revision(self.telescope, False, "2023-02-10 00:00:00")
        self._update_telescope_revision(self.telescope, True, "2023-03-10 00:00:00")

        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?telescope_id={self.telescope.code}&site_id={self.site.code}&enclosure_id={self.enclosure.code}')
        expected_intervals = {'availability_intervals': [
            {'start': datetime(2023, 3, 10).isoformat(), 'end': datetime(2024, 1, 1).isoformat()},
            {'start': datetime(2023, 1, 1).isoformat(), 'end': datetime(2023, 2, 1).isoformat()}]}
        self.assertEqual(response.json(), expected_intervals)

    def test_multiple_instrument_availability_history(self):
        # Add a second instrument on the telescope that is always available and see that the telescope shows always available
        instrument_2 = mixer.blend(Instrument, autoguider_camera=self.camera, telescope=self.telescope,
                                   instrument_type=self.instrument_type, science_cameras=[self.camera],
                                   state=Instrument.SCHEDULABLE, code='myInst02')
        with time_machine.travel("2023-01-01 00:00:00"):
            with reversion.create_revision():
                instrument_2.save()
        self._update_instrument_revision(self.instrument, Instrument.MANUAL, "2023-02-01 00:00:00")
        self._update_instrument_revision(self.instrument, Instrument.SCHEDULABLE, "2023-03-01 00:00:00")

        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?telescope_id={self.telescope.code}&site_id={self.site.code}&enclosure_id={self.enclosure.code}')
        expected_intervals = {'availability_intervals': [
            {'start': datetime(2023, 1, 1).isoformat(), 'end': datetime(2024, 1, 1).isoformat()}]}
        self.assertEqual(response.json(), expected_intervals)
