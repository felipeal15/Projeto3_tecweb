from rest_framework import serializers

from .models import Vaga


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
