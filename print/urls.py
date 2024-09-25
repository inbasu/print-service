from django.urls import path

from print.views import (
    PrinterCRUD,
    PrintersList,
    PrintLabel,
    SmartPrint,
    UpdateApp,
    UpdateLabel,
)

"""
Юрлы не конситентны, т.к. подстраивался под старое приложение
"""

urlpatterns = [
    path("printer/run/", PrintersList.as_view()),
    path("printlabel/run/", PrintLabel.as_view()),
    path("printlabel/run/smart/", SmartPrint.as_view()),
    path("printer/crud/", PrinterCRUD.as_view()),
    path("print/update/label/", UpdateLabel.as_view()),
    path("print/update/app/", UpdateApp.as_view()),
]
