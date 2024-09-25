from rest_framework.serializers import ModelSerializer

from print.models import Printer


class PrinterSerializer(ModelSerializer):
    class Meta:
        model = Printer
        fields = ["name", "ip"]
