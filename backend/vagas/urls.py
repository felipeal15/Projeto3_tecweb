from django.urls import path

from . import views

urlpatterns = [
    path("vagas/", views.api_vagas),
    path("vagas/<int:vaga_id>/", views.api_vaga),
    path("vagas/<int:vaga_id>/analise/", views.api_analise),
    path("vagas/<int:vaga_id>/carta/", views.api_carta),
    path("curriculo/", views.api_curriculo),
    path("curriculo/pdf/", views.api_curriculo_pdf),
    path("sugestoes/", views.api_sugestoes),
    path("vagas-reais/", views.api_vagas_reais),
]
