from rest_framework import serializers

from .models import Analise, Curriculo, Vaga


class VagaSerializer(serializers.ModelSerializer):
    # Nota (0 a 100) da análise mais recente, para o card do kanban. null se ainda não foi analisada.
    ultima_nota = serializers.SerializerMethodField()

    class Meta:
        model = Vaga
        fields = [
            "id",
            "titulo",
            "empresa",
            "local",
            "link",
            "descricao",
            "status",
            "ultima_nota",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em"]

    def get_ultima_nota(self, vaga):
        # As views já trazem a nota calculada no banco (vagas_do_usuario).
        if hasattr(vaga, "nota_mais_recente"):
            return vaga.nota_mais_recente
        analise = vaga.analises.first()
        return analise.nota if analise else None


class CurriculoSerializer(serializers.ModelSerializer):
    # true quando o texto mudou depois da última estruturação pela IA.
    desatualizado = serializers.SerializerMethodField()

    class Meta:
        model = Curriculo
        fields = ["texto", "dados", "desatualizado", "atualizado_em"]
        read_only_fields = ["dados", "atualizado_em"]

    def validate_texto(self, texto):
        texto = texto.strip()
        if len(texto) < 50:
            raise serializers.ValidationError("Cole o currículo completo (pelo menos 50 caracteres).")
        return texto

    def get_desatualizado(self, curriculo):
        return curriculo.hash_dados != curriculo.hash_texto


class ResultadoAnaliseSerializer(serializers.Serializer):
    """Valida o JSON que a IA devolve antes de salvar a análise."""

    nota = serializers.IntegerField(min_value=0, max_value=100)
    resumo = serializers.CharField()
    requisitos_atendidos = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    lacunas = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    sugestoes = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class AnaliseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analise
        fields = ["id", "vaga", "nota", "resultado", "modelo_ia", "versao_prompt", "criado_em"]
