import time

from celery import shared_task

from print.models import Printer


# celery -A core worker -P eventlet -l INFO --concurrency=10


@shared_task()
def print_label(ip: str, labels: list[str]) -> None:
    printer = Printer.objects.get(ip=ip)
    for label in labels:
        printer.print(label)
        time.sleep(0.8)
