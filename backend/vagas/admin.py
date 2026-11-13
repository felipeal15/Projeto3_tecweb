from django.contrib import admin

from .models import Analise, Curriculo, Vaga


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "empresa", "status", "usuario", "atualizado_em"]
    list_filter = ["status"]
    search_fields = ["titulo", "empresa"]


@admin.register(Curriculo)
class CurriculoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "atualizado_em"]


@admin.register(Analise)
class AnaliseAdmin(admin.ModelAdmin):
    list_display = ["vaga", "nota", "modelo_ia", "versao_prompt", "criado_em"]
