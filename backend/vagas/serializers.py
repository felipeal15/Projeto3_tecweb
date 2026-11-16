from rest_framework import serializers

from .models import Analise, Carta, Curriculo, Vaga


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


def mudou_desde(objeto, curriculo):
    """True se o currículo ou a vaga mudaram depois que `objeto` (Analise ou Carta) foi gerado."""
    hash_curriculo_atual = curriculo.hash_texto if curriculo else ""
    return (
        objeto.hash_curriculo != hash_curriculo_atual
        or objeto.hash_vaga != objeto.vaga.hash_conteudo
    )


class AnaliseSerializer(serializers.ModelSerializer):
    # true quando o currículo ou a vaga mudaram depois desta análise.
    desatualizada = serializers.SerializerMethodField()

    class Meta:
        model = Analise
        fields = [
            "id",
            "vaga",
            "nota",
            "resultado",
            "desatualizada",
            "modelo_ia",
            "versao_prompt",
            "criado_em",
        ]

    def get_desatualizada(self, analise):
        return mudou_desde(analise, analise.curriculo)


class GerarCartaSerializer(serializers.Serializer):
    """O que o frontend manda para gerar a carta (os dois campos são opcionais)."""

    tom = serializers.ChoiceField(choices=Carta.Tom.choices, default=Carta.Tom.NEUTRO)
    tamanho = serializers.ChoiceField(choices=Carta.Tamanho.choices, default=Carta.Tamanho.CURTA)


class ResultadoCartaSerializer(serializers.Serializer):
    """Valida o JSON da carta que a IA devolve antes de salvar."""

    carta = serializers.CharField(min_length=100)
    fatos_usados = serializers.ListField(child=serializers.CharField(), allow_empty=False)


class CartaSerializer(serializers.ModelSerializer):
    # true quando o usuário mudou o texto que a IA escreveu.
    editada = serializers.SerializerMethodField()
    # true quando o currículo ou a vaga mudaram depois que a carta foi gerada.
    desatualizada = serializers.SerializerMethodField()

    class Meta:
        model = Carta
        fields = [
            "id",
            "vaga",
            "texto",
            "fatos_usados",
            "tom",
            "tamanho",
            "editada",
            "desatualizada",
            "modelo_ia",
            "versao_prompt",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "vaga",
            "fatos_usados",
            "tom",
            "tamanho",
            "modelo_ia",
            "versao_prompt",
            "criado_em",
            "atualizado_em",
        ]

    def validate_texto(self, texto):
        texto = texto.strip()
        if not texto:
            raise serializers.ValidationError("A carta não pode ficar vazia.")
        if len(texto) > 6000:
            raise serializers.ValidationError("A carta passou de 6000 caracteres. Encurte um pouco.")
        return texto

    def get_editada(self, carta):
        return carta.texto != carta.texto_gerado

    def get_desatualizada(self, carta):
        curriculo = Curriculo.objects.filter(usuario_id=carta.vaga.usuario_id).first()
        return mudou_desde(carta, curriculo)
