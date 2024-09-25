import logging
import re
import socket
import subprocess

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

printers_update_logger = logging.getLogger("printers_update")


# Create your modelmanagers here.
class LabelModelManager(models.Manager):
    def update_or_create(self, **obj_data):
        try:
            obj_data["defaults"]["Label_App"] = Label_App.objects.get(Mask_App=obj_data["defaults"]["Label_App"])
            return super().update_or_create(**obj_data)
        except ObjectDoesNotExist:
            printers_update_logger.warning(obj_data)
            return None


# Create your models here.
class ZplField(models.Model):
    name = models.CharField(max_length=16, blank=False, null=False)
    placeholder = models.CharField(max_length=16, blank=False, null=False)

    def __str__(self) -> str:
        return f"{self.name}\t{self.placeholder}"


class Label_App(models.Model):
    Name = models.CharField(max_length=32, unique=True, blank=False, null=False)
    Mask_App = models.CharField(max_length=32, blank=False, null=False)
    Mask_PRS = models.CharField(max_length=24, blank=False, null=False)

    def __str__(self) -> str:
        return str(self.Name)


class Label(models.Model):
    Name = models.CharField(max_length=64, unique=True, blank=False, null=False)
    Label_Type = models.CharField(max_length=32, blank=False, null=False)
    Label_App = models.ForeignKey(to=Label_App, on_delete=models.CASCADE, blank=False, null=False)
    Label_ID = models.CharField(max_length=12, null=False, blank=False)
    ZPL_Text = models.TextField()

    objects = LabelModelManager()

    def __str__(self) -> str:
        return str(self.Name)

    def form_zpl(self, data: dict) -> str:
        """
        Некторые поля приходиться корректировать вручную
        """
        zpl: str = self.ZPL_Text
        fields: list[ZplField] = ZplField.objects.all()
        for field in fields:
            value: str = data.get(field.name, "")
            if value:
                match field.name:
                    case "МВП":
                        zpl = zpl.replace(field.placeholder, value[-4:])
                    case _:
                        zpl = zpl.replace(field.placeholder, value)
        for field in fields:
            if field.placeholder in zpl:
                zpl = zpl.replace(field.placeholder, "")
        return zpl


class Printer(models.Model):
    name = models.CharField(max_length=64, unique=True, null=False, blank=False)
    ip = models.CharField(max_length=15, null=False)
    Label_App = models.ForeignKey(to=Label_App, on_delete=models.CASCADE, blank=True)
    Label_ID = models.CharField(max_length=12, null=False, blank=False)

    class Meta:
        verbose_name = "Printer"
        verbose_name_plural = "Printers"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def clean(self, *args, **kwargs):
        self.validate_ip()
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            self.Label_ID = self.name.split("_")[-1].strip()
            self.Label_App = self.get_print_label_app()
            self.full_clean()
            super().save(*args, **kwargs)
        except ObjectDoesNotExist:
            raise ValidationError(f"Problem during validation printer Name")

    def online(self) -> bool:
        args = ["ping", "-n", "1", self.ip]
        stdout: str = subprocess.run(args, capture_output=True).stdout.decode("cp437", "ignore")
        return not bool("100% loss" in stdout)

    def get_label(self, **kwargs) -> Label | None:
        try:
            return Label.objects.get(labelApp=self.Label_App, label_ID=self.Label_ID, **kwargs)
        except ObjectDoesNotExist:
            return None

    def print(self, label: str) -> None:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((self.ip, 9100))
        soc.send(bytes(label, "utf-8"))
        soc.close()

    # Validations
    def get_print_label_app(self) -> "Label_App":
        for app in Label_App.objects.all():
            if app.Mask_PRS in self.name:
                return app
        raise ObjectDoesNotExist()

    def validate_ip(self) -> str:
        if posible_ip := re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", self.ip):
            return posible_ip
        raise ValidationError("Problem during validation printer IP")
