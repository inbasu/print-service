from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/", include("mail.urls")),
    path("api/", include("print.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
