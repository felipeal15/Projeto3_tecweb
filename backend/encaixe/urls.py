from django.contrib import admin
from django.urls import include, path

from contas.views import preferencias

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("contas.urls")),
    path("api/preferencias/", preferencias),
    path("api/", include("vagas.urls")),
]
