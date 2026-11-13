from django.urls import path

from . import views

urlpatterns = [
    path("vagas/", views.api_vagas),
    path("vagas/<int:vaga_id>/", views.api_vaga),
    path("vagas/<int:vaga_id>/analise/", views.api_analise),
    path("curriculo/", views.api_curriculo),
]
