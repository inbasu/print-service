from django.test import TestCase
from rest_framework.test import APIClient

from print.models import Label_App, Printer


class CrudTest(TestCase):
    requests = APIClient()
    url = "/api/printer/crud/"

    def test_succ_create(self):
        Label_App.objects.create(Name="IT", Mask_App="IT", Mask_PRS="Invent_IT")
        resp = self.requests.post(self.url, {"name": "1033_Invent_IT_ZBR1", "ip": "10.204.202.32"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["ok"], "ok")
        self.assertEqual(resp.data["1033_Invent_IT_ZBR1"], {"name": "1033_Invent_IT_ZBR1", "ip": "10.204.202.32"})
        printer = Printer.objects.last()
        self.assertEqual(printer.Label_App.Name, "IT")
        self.assertEqual(printer.Label_ID, "ZBR1")

    # def test_fail_create(self):
    #     self.assertTrue(False)

    def test_succ_update(self):
        created = Printer.objects.create(
            name="1033_Invent_IT_ZBR1",
            ip="10.204.202.32",
            Label_ID="ZBR1",
            Label_App=Label_App.objects.get_or_create(Name="IT", Mask_App="IT", Mask_PRS="Invent_IT")[0],
        )
        resp = self.requests.post(self.url, {"name": "1033_Invent_IT_ZBR1", "ip": "10.204.202.33"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["ok"], "ok")
        updated = Printer.objects.last()
        self.assertNotEqual(created.ip, updated.ip)
        self.assertEqual(updated.ip, "10.204.202.33")

    # def test_fail_update(self):
    #     self.assertTrue(False)

    def test_succ_delete(self):
        created = Printer.objects.create(
            name="1033_Invent_IT_ZBR1",
            ip="10.204.202.32",
            Label_ID="ZBR1",
            Label_App=Label_App.objects.get_or_create(Name="IT", Mask_App="IT", Mask_PRS="Invent_IT")[0],
        )
        self.assertEqual(created, Printer.objects.last())
        resp = self.requests.delete(self.url, {"name": "1033_Invent_IT_ZBR1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["ok"], "ok")
        self.assertNotEqual(created, Printer.objects.last())

    # def test_fail_delete(self):
    #     self.assertTrue(False)
