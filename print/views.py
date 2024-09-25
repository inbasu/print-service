import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest

# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from print.models import Label, Label_App, Printer
from print.serializers import PrinterSerializer
from print.tasks import print_label

printers_update_logger = logging.getLogger("printers_update")

from utils.insight import mars


# Create your views here.
class PrintersList(APIView):
    renderer_classes = [JSONRenderer]
    http_method_names = ["get"]

    def get(self, request: HttpRequest) -> Response:
        priners = Printer.objects.all()
        for exp in request.GET.get("mask", "").split("*"):
            priners = priners.filter(name__contains=exp)  # ?
        return Response(
            {printer["name"]: printer for printer in PrinterSerializer(priners, many=True).data},
            status=status.HTTP_200_OK,
        )


class PrintLabel(APIView):
    renderer_classes = [JSONRenderer]
    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> Response:
        ip, zpl = request.data.get("ip", ""), request.data.get("zpl", "")
        try:
            printer = Printer.objects.get(ip=ip)
            if zpl and printer and printer.online():
                printer.print(zpl)
                return Response({"ok": "ok", "error": ""}, status=status.HTTP_200_OK)
        finally:
            return Response({"ok": "Not ok", "error": "bad data"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateLabel(APIView):
    renderer_classes = [JSONRenderer]
    http_method_names = ["get"]

    def get(self, requset: HttpRequest) -> Response:
        # TODO Check printers that not updated and delete unused or mark them
        labels: list[dict] = mars.search(item_type=234, scheme=1)
        updated = 0
        for label in labels:
            if name := label.get("Name", ""):
                data = {
                    field: label[field] for field in [f.name for f in Label._meta.get_fields()] if label.get(field, "")
                }
                _, created = Label.objects.update_or_create(Name=name, defaults=data)
                if created:
                    updated += 1
        printers_update_logger.info(f"total: {len(labels)}, updated: {len(labels)-updated}, created: {updated}")
        return Response({"ok": "ok", "error": ""}, status=status.HTTP_200_OK)


class UpdateApp(APIView):
    renderer_classes = [JSONRenderer]
    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> Response:
        return Response({})


class PrinterCRUD(APIView):
    renderer_classes = [JSONRenderer]
    http_method_names = ["delete", "post", "put"]

    def post(self, request: HttpRequest) -> Response:
        if name := request.data.get("name", ""):
            data = {
                field: request.data[field]
                for field in [f.name for f in Printer._meta.get_fields()]
                if request.data.get(field, "")
            }
            try:
                printer, _ = Printer.objects.update_or_create(name=name, defaults=data)
            except Exception as e:
                printers_update_logger.warning(e)
            return Response({"ok": "ok", "error": "", name: PrinterSerializer(printer).data}, status=status.HTTP_200_OK)
        return Response({"ok": "Not ok", "error": "Bad data"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: HttpRequest) -> Response:
        try:
            name = request.data.get("name")
            Printer.objects.get(name=name).delete()
            return Response({"ok": "ok", "error": ""}, status=status.HTTP_200_OK)
        except KeyError:
            return Response({"ok": "Not ok", "error": "no name field"}, status=status.HTTP_400_BAD_REQUEST)
        except Printer.ObjectDoesNotExist:
            return Response(
                {"ok": "Not ok", "error": f"no printer with name {name}"}, status=status.HTTP_400_BAD_REQUEST
            )


class SmartPrint(APIView):

    renderer_classes = [JSONRenderer]
    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> Response:
        data = json.loads(request.data)
        try:
            printer = Printer.objects.get(name=data.get("PrinterName", ""))
            label = Label.objects.get(
                Label_App=printer.Label_App,
                Label_ID=printer.Label_ID,
                Label_Type=data.get("LabelType"),
            )
        except ObjectDoesNotExist:
            # TODO Разделить ошибку на 2 для принтера и этикетки
            return Response({"ok": "Not ok", "error": "Printer data is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response({"ok": "Not ok", "error": "Forget LabelType?"}, status=status.HTTP_400_BAD_REQUEST)
        if not printer.online():
            return Response({"ok": "Not ok", "error": "Printer offline"})
        items = self.prepare_data(data["data"], printer.Label_App)
        if zpls := [label.form_zpl(item) for item in items]:
            print_label.delay(printer.ip, zpls)
            return Response({"ok": "ok", "error": ""}, status=status.HTTP_200_OK)
        return Response({"ok": "Not ok", "error": "Isight objects data error"}, status=status.HTTP_400_BAD_REQUEST)

    # Change code below
    def prepare_data(self, data, app: Label_App) -> list[dict]:
        match data:
            case list():
                if isinstance(data[0], (int, str)):
                    obj_data = {
                        "iql": f'"Key" in ({(',').join(data)})' if app.Mask_App == "IT" else "",
                        "scheme": 1 if app.Mask_App == "IT" else 9,
                        "item_type": 8 if app.Mask_App == "IT" else 142,
                    }
                    return mars.search(**obj_data)
                elif isinstance(data[0], dict):
                    return data
                return []
            case dict():
                return [data]
            case str() | int():
                obj_data = {
                    "iql": f'"Key" = "{data}"' if app.Mask_App == "IT" else "",
                    "scheme": 1 if app.Mask_App == "IT" else 9,
                    "item_type": 8 if app.Mask_App == "IT" else 142,
                }
                return mars.search(**obj_data)
        return []
