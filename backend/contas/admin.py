from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["nome", "usuario", "criado_em"]
    search_fields = ["nome", "usuario__email"]
