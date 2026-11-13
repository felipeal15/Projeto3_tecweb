from django.urls import path

from . import views

urlpatterns = [
    path("cadastro/", views.cadastro),
    path("login/", views.login),
    path("logout/", views.logout),
    path("eu/", views.eu),
]
