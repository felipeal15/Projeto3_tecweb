from django.urls import path

from . import views

urlpatterns = [
    path("vagas/", views.api_vagas),
    path("vagas/<int:vaga_id>/", views.api_vaga),
]
