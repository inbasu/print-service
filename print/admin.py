from django.contrib import admin

from print.models import Label, Label_App, Printer, ZplField

# Register your models here.
for model in {Printer, Label, Label_App, ZplField}:
    admin.site.register(model)
