from django.contrib import admin

from .models import Perfil, Preferencias


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["nome", "usuario", "criado_em"]
    search_fields = ["nome", "usuario__email"]


@admin.register(Preferencias)
class PreferenciasAdmin(admin.ModelAdmin):
    list_display = ["usuario", "cidade", "atualizado_em"]
    search_fields = ["usuario__email", "cidade"]
