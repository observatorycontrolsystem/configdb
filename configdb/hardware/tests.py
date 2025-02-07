import json
import reversion
import time_machine
from datetime import datetime
from http import HTTPStatus
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from .models import (Site, Instrument, Enclosure, Telescope, Camera, CameraType, InstrumentType,
                     GenericMode, GenericModeGroup, ModeType, OpticalElement, OpticalElementGroup,
                     ConfigurationType, ConfigurationTypeProperties, InstrumentCategory)
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
        mixer.blend(Instrument, autoguider_camera=self.camera, telescope=self.telescope,
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


class TestCreationThroughAPI(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

    def test_create_optical_element(self):
        optical_element = {'code': 'Ha', 'name': 'H-Alpha', 'schedulable': True}
        response = self.client.post(reverse('opticalelement-list'), data=optical_element)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(OpticalElement.objects.all().count(), 1)
        oe = OpticalElement.objects.first()
        self.assertEqual(oe.code, optical_element['code'])
        self.assertEqual(oe.name, optical_element['name'])
        self.assertEqual(oe.schedulable, optical_element['schedulable'])
        # Try to create the same optical element again and it will fail since code isn't unique
        response = self.client.post(reverse('opticalelement-list'), data=optical_element)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_create_optical_element_group(self):
        # Create an optical element group with 2 optical elements
        optical_element1 = {'code': 'Ha', 'name': 'H-Alpha', 'schedulable': True}
        optical_element2 = {'code': 'r', 'name': 'Red', 'schedulable': True}
        optical_element_group = {'name': 'myGroup', 'type': 'filters',
                                 'optical_elements': [optical_element1, optical_element2]}
        response = self.client.post(reverse('opticalelementgroup-list'),
                                    data=optical_element_group, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(OpticalElement.objects.all().count(), 2)
        self.assertEqual(OpticalElementGroup.objects.all().count(), 1)
        oeg = OpticalElementGroup.objects.first()
        self.assertEqual(oeg.default, None)
        self.assertEqual(oeg.name, optical_element_group['name'])
        self.assertEqual(oeg.optical_elements.first().code, optical_element1['code'])
        self.assertEqual(oeg.optical_elements.last().code, optical_element2['code'])

        # Now update the default value
        default = {'default': optical_element2['code']}
        response = self.client.patch(reverse('opticalelementgroup-detail', args=(oeg.id,)), data=default)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        oeg.refresh_from_db()
        self.assertEqual(oeg.default.code, optical_element2['code'])

        # Now create another optical element group re-using the same two optical elements
        optical_element_group2 = {'name': 'secondGroup', 'type': 'filters',
                                  'optical_elements': [optical_element1, optical_element2]}
        response = self.client.post(reverse('opticalelementgroup-list'),
                                    data=optical_element_group2, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        # See that there are still only 2 optical elements in the db
        self.assertEqual(OpticalElement.objects.all().count(), 2)
        self.assertEqual(OpticalElementGroup.objects.all().count(), 2)

    def test_create_optical_element_group_from_existing_optical_elements(self):
        # Create an optical element group with 2 optical elements
        optical_element1 = mixer.blend(OpticalElement)
        optical_element2 = mixer.blend(OpticalElement)
        optical_element_group = {'name': 'myGroup', 'type': 'filters', 'default': optical_element1.code,
                                 'optical_element_ids': [optical_element1.id, optical_element2.id]}
        response = self.client.post(reverse('opticalelementgroup-list'),
                                    data=optical_element_group, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(OpticalElement.objects.all().count(), 2)
        self.assertEqual(OpticalElementGroup.objects.all().count(), 1)
        oeg = OpticalElementGroup.objects.first()
        self.assertEqual(oeg.default.code, optical_element1.code)
        self.assertEqual(oeg.name, optical_element_group['name'])
        self.assertEqual(oeg.optical_elements.first().code, optical_element1.code)
        self.assertEqual(oeg.optical_elements.last().code, optical_element2.code)

    def test_default_mode_types_exist(self):
        response = self.client.get(reverse('modetype-list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()['count'], 5)
        self.assertContains(response, 'readout')
        self.assertContains(response, 'guiding')
        self.assertContains(response, 'acquisition')
        self.assertContains(response, 'exposure')
        self.assertContains(response, 'rotator')

    def test_create_mode_type(self):
        mode_type = {'id': 'newMode'}
        response = self.client.post(reverse('modetype-list'), data=mode_type, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(response.json()['id'], mode_type['id'])
        self.assertEqual(ModeType.objects.all().count(), 6)

    def test_create_generic_mode(self):
        generic_mode = {'name': 'testMode', 'code': 'tM', 'schedulable': True, 'overhead': 45.0,
                        'validation_schema': {}}
        response = self.client.post(reverse('genericmode-list'), data=generic_mode, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(GenericMode.objects.all().count(), 1)
        self.assertEqual(response.json()['code'], generic_mode['code'])
        self.assertEqual(response.json()['overhead'], generic_mode['overhead'])
        self.assertEqual(response.json()['name'], generic_mode['name'])
        self.assertEqual(response.json()['schedulable'], generic_mode['schedulable'])

    def test_create_generic_mode_group(self):
        instrument_type = mixer.blend(InstrumentType)
        generic_mode1 = {'name': 'testMode', 'code': 'tM'}
        generic_mode2 = {'name': 'testMode2', 'code': 'tM2'}
        generic_mode_group = {'type': 'readout', 'instrument_type': instrument_type.id,
                              'modes': [generic_mode1, generic_mode2]}
        response = self.client.post(reverse('genericmodegroup-list'), data=generic_mode_group, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(GenericMode.objects.all().count(), 2)
        self.assertEqual(GenericModeGroup.objects.all().count(), 1)
        gmg = GenericModeGroup.objects.first()
        self.assertEqual(gmg.default, None)
        self.assertEqual(gmg.type.id, generic_mode_group['type'])
        self.assertEqual(gmg.instrument_type.code, instrument_type.code)
        self.assertEqual(gmg.modes.first().code, generic_mode1['code'])
        self.assertEqual(gmg.modes.last().code, generic_mode2['code'])
        # Now update the default value
        default = {'default': generic_mode2['code']}
        response = self.client.patch(reverse('genericmodegroup-detail', args=(gmg.id,)), data=default)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        gmg.refresh_from_db()
        self.assertEqual(gmg.default.code, generic_mode2['code'])

        # Now create another optical element group re-using the same two optical elements
        instrument_type2 = mixer.blend(InstrumentType)
        generic_mode_group2 = {'type': 'readout', 'instrument_type': instrument_type2.id,
                               'modes': [generic_mode1, generic_mode2]}
        response = self.client.post(reverse('genericmodegroup-list'), data=generic_mode_group2, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        # See that there are still only 2 generic modes in the db
        self.assertEqual(GenericMode.objects.all().count(), 2)
        self.assertEqual(GenericModeGroup.objects.all().count(), 2)

    def test_create_generic_mode_group_from_existing_modes(self):
        instrument_type = mixer.blend(InstrumentType)
        mode1 = mixer.blend(GenericMode)
        mode2 = mixer.blend(GenericMode)
        # Since the modes are existing, we can set the default in the initial creation
        generic_mode_group = {'type': 'readout', 'instrument_type': instrument_type.id,
                              'mode_ids': [mode1.id, mode2.id], 'default': mode1.code}
        response = self.client.post(reverse('genericmodegroup-list'), data=generic_mode_group, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(GenericMode.objects.all().count(), 2)
        self.assertEqual(GenericModeGroup.objects.all().count(), 1)
        gmg = GenericModeGroup.objects.first()
        self.assertEqual(gmg.default.code, mode1.code)
        self.assertEqual(gmg.type.id, generic_mode_group['type'])
        self.assertEqual(gmg.instrument_type.code, instrument_type.code)
        self.assertEqual(gmg.modes.first().code, mode1.code)
        self.assertEqual(gmg.modes.last().code, mode2.code)

    def test_create_configuration_type(self):
        configuration_type = {'name': 'Repeat Exposure', 'code': 'REPEAT_EXPOSE'}
        response = self.client.post(reverse('configurationtype-list'), data=configuration_type)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(ConfigurationType.objects.all().count(), 1)
        self.assertEqual(response.json()['code'], configuration_type['code'])

    def test_create_configuration_type_must_have_unique_code(self):
        config_type = mixer.blend(ConfigurationType)
        configuration_type = {'name': 'Repeat Exposure', 'code': config_type.code}
        response = self.client.post(reverse('configurationtype-list'), data=configuration_type)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertIn('configuration type with this code already exists.', response.json()['code'])

    def test_create_configuration_type_properties(self):
        config_type = mixer.blend(ConfigurationType)
        inst_type = mixer.blend(InstrumentType)
        configuration_type_properties = {
            'configuration_type': config_type.code, 'instrument_type': inst_type.id,
            'config_change_overhead': 33.3, 'schedulable': False
        }
        response = self.client.post(reverse('configurationtypeproperties-list'), data=configuration_type_properties, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(ConfigurationTypeProperties.objects.all().count(), 1)
        self.assertEqual(response.json()['configuration_type'], config_type.code)
        self.assertEqual(response.json()['instrument_type'], inst_type.id)
        self.assertEqual(response.json()['config_change_overhead'], 33.3)

    def test_create_configuration_type_properties_must_be_unique(self):
        config_type = mixer.blend(ConfigurationType)
        inst_type = mixer.blend(InstrumentType)
        mixer.blend(ConfigurationTypeProperties, configuration_type=config_type, instrument_type=inst_type)
        configuration_type_properties = {
            'configuration_type': config_type.code, 'instrument_type': inst_type.id,
            'config_change_overhead': 33.3, 'schedulable': False
        }
        response = self.client.post(reverse('configurationtypeproperties-list'), data=configuration_type_properties, format='json')
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertIn('The fields instrument_type, configuration_type must make a unique set', response.json()['non_field_errors'][0])

    def test_create_instrument_category(self):
        instrument_category = {'code': 'IMAGE'}
        response = self.client.post(reverse('instrumentcategory-list'), data=instrument_category)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(InstrumentCategory.objects.all().count(), 1)
        self.assertEqual(response.json()['code'], instrument_category['code'])

    def test_create_instrument_category_must_have_unique_code(self):
        inst_category = mixer.blend(InstrumentCategory)
        instrument_category = {'code': inst_category.code}
        response = self.client.post(reverse('instrumentcategory-list'), data=instrument_category)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertIn('instrument category with this code already exists.', response.json()['code'])

    def test_create_simple_instrument_type(self):
        inst_category = mixer.blend(InstrumentCategory)
        instrument_type = {
            'name': 'MyTestInstrumentType',
            'code': 'test01',
            'instrument_category': inst_category.code
        }
        response = self.client.post(reverse('instrumenttype-list'), data=instrument_type)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(InstrumentType.objects.all().count(), 1)
        self.assertEqual(response.json()['code'], instrument_type['code'])

    def test_create_instrument_type_with_configuration_types(self):
        inst_category = mixer.blend(InstrumentCategory)
        config_type1 = mixer.blend(ConfigurationType)
        config_type2 = mixer.blend(ConfigurationType)

        instrument_type = {
            'name': 'MyTestInstrumentType',
            'code': 'test01',
            'instrument_category': inst_category.code,
            'configuration_types': [
                {'configuration_type': config_type1.code, 'schedulable': True, 'config_change_overhead': 45.0},
                {'configuration_type': config_type2.code, 'schedulable': True, 'config_change_overhead': 5.0},
            ]
        }
        response = self.client.post(reverse('instrumenttype-list'), data=instrument_type, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(InstrumentType.objects.all().count(), 1)
        self.assertEqual(ConfigurationTypeProperties.objects.all().count(), 2)
        self.assertEqual(response.json()['code'], instrument_type['code'])
        self.assertEqual(response.json()['instrument_category'], inst_category.code)
        self.assertEqual(response.json()['configuration_types'][1]['code'], config_type2.code)
        self.assertEqual(response.json()['configuration_types'][1]['config_change_overhead'], 5.0)

    def test_patch_instrument_type(self):
        inst_category1 = mixer.blend(InstrumentCategory)
        inst_category2 = mixer.blend(InstrumentCategory)
        config_type1 = mixer.blend(ConfigurationType)
        config_type2 = mixer.blend(ConfigurationType)
        instrument_type = mixer.blend(InstrumentType, instrument_category=inst_category1)
        ctp1 = mixer.blend(ConfigurationTypeProperties, configuration_type=config_type1, instrument_type=instrument_type)
        updates = {
            'name': 'MyInstType',
            'observation_front_padding': 12.3,
            'instrument_category': inst_category2.code,
            'allow_self_guiding': False,
            'configuration_types': [{'configuration_type': config_type2.code, 'config_change_overhead': 6.6}]
        }
        response = self.client.patch(reverse('instrumenttype-detail', args=(instrument_type.id,)), data=updates, format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        it = InstrumentType.objects.first()
        self.assertEqual(it.name, updates['name'])
        self.assertEqual(it.instrument_category.code, inst_category2.code)
        self.assertEqual(it.observation_front_padding, updates['observation_front_padding'])
        self.assertEqual(it.configuration_types.first().code, config_type2.code)
        self.assertEqual(response.json()['configuration_types'][0]['config_change_overhead'], 6.6)


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
            response = self.client.get(reverse('availability') + '?instrument_id=FakeInst')
        self.assertContains(response, 'No instrument found with code FakeInst', status_code=404)

    def test_requires_telescope_to_exist(self):
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?telescope_id=FakeCode&site_id={self.site.code}&enclosure_id={self.enclosure.code}')
        self.assertContains(response, f'No telescope found with code {self.site.code}.{self.enclosure.code}.FakeCode', status_code=404)

    def test_requires_date_params_be_parseable(self):
        with time_machine.travel("2024-01-01 00:00:00"):
            response = self.client.get(reverse('availability') + f'?instrument_id={self.instrument.code}&start=notadate')
        self.assertContains(response, 'The format used for the start/end parameters is not parseable', status_code=400)

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
