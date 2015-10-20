from django.test import TestCase
from django.test import Client


class SimpleHardwareTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertContains(response, 'ConfigDB3', status_code=200)
