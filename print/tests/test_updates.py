from django.test import TestCase
from rest_framework.test import APIClient

from print.models import Label


class CrudTest(TestCase):
    requests = APIClient()
    url = "/api/print/update/label/"

    def test_succ_update_label(self):
        base = len(Label.objects.all())
        resp = self.requests.get(self.url)
        self.assertEqual(200, resp.status_code)
        self.assertNotEqual(len(Label.objects.all()), base)
