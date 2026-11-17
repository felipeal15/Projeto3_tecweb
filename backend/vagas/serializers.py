from rest_framework import serializers

from contas.models import Preferencias, hash_preferencias

from .busca import links_de_busca
from .compatibilidade import fora_das_preferencias
from .models import Analise, Carta, Curriculo, Sugestoes, Vaga

SEM_CONTEXTO = object()


class VagaSerializer(serializers.ModelSerializer):
    # Nota (0 a 100) da análise mais recente, para o card do kanban. null se ainda não foi analisada.
    ultima_nota = serializers.SerializerMethodField()
    # O que na vaga vai contra as preferências (ex.: ["Presencial"]); [] = combina ou não dá para saber.
    fora_das_preferencias = serializers.SerializerMethodField()

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
            "fora_das_preferencias",
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

    def get_fora_das_preferencias(self, vaga):
        # As views passam as preferências no contexto, para não buscar uma vez por vaga.
        preferencias = self.context.get("preferencias", SEM_CONTEXTO)
        if preferencias is SEM_CONTEXTO:
            preferencias = Preferencias.do_usuario(vaga.usuario_id)
        return fora_das_preferencias(vaga, preferencias)


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
    # Pontos da vaga que vão contra as preferências do usuário (prompt v2).
    alertas_preferencias = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, required=False, default=list
    )


def mudou_desde(objeto, curriculo):
    """True se o currículo ou a vaga mudaram depois que `objeto` (Analise ou Carta) foi gerado."""
    hash_curriculo_atual = curriculo.hash_texto if curriculo else ""
    return (
        objeto.hash_curriculo != hash_curriculo_atual
        or objeto.hash_vaga != objeto.vaga.hash_conteudo
    )


class AnaliseSerializer(serializers.ModelSerializer):
    # true quando o currículo, a vaga ou as preferências mudaram depois desta análise.
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
        return mudou_desde(analise, analise.curriculo) or (
            analise.hash_preferencias != hash_preferencias(analise.vaga.usuario_id)
        )


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


class CargoSugeridoSerializer(serializers.Serializer):
    """Um cargo sugerido pela IA (valida o JSON antes de salvar)."""

    cargo = serializers.CharField(max_length=120)
    area = serializers.CharField(max_length=80, allow_blank=True, required=False, default="")
    nota = serializers.IntegerField(min_value=0, max_value=100)
    por_que = serializers.CharField()
    busca = serializers.CharField(max_length=80)
    palavras_chave = serializers.ListField(child=serializers.CharField(max_length=60), allow_empty=True)


class ResultadoSugestoesSerializer(serializers.Serializer):
    cargos = CargoSugeridoSerializer(many=True, allow_empty=False)

    def validate_cargos(self, cargos):
        # Maior nota primeiro, no máximo 6 cards e 6 palavras-chave por card.
        cargos = sorted(cargos, key=lambda cargo: cargo["nota"], reverse=True)[:6]
        return [{**cargo, "palavras_chave": cargo["palavras_chave"][:6]} for cargo in cargos]


class SugestoesSerializer(serializers.ModelSerializer):
    """Sugestões salvas, com os links de busca montados a partir das preferências atuais."""

    cargos = serializers.SerializerMethodField()
    # true quando o currículo ou as preferências mudaram depois que as sugestões foram geradas.
    desatualizada = serializers.SerializerMethodField()

    class Meta:
        model = Sugestoes
        fields = ["cargos", "desatualizada", "modelo_ia", "versao_prompt", "atualizado_em"]

    def preferencias(self, sugestoes):
        preferencias = self.context.get("preferencias", SEM_CONTEXTO)
        if preferencias is SEM_CONTEXTO:
            preferencias = Preferencias.do_usuario(sugestoes.usuario_id)
        return preferencias

    def get_cargos(self, sugestoes):
        preferencias = self.preferencias(sugestoes)
        return [
            {**cargo, "links": links_de_busca(cargo["busca"], preferencias)}
            for cargo in sugestoes.cargos
        ]

    def get_desatualizada(self, sugestoes):
        curriculo = Curriculo.objects.filter(usuario_id=sugestoes.usuario_id).first()
        preferencias = self.preferencias(sugestoes)
        return (curriculo is None or sugestoes.hash_curriculo != curriculo.hash_texto) or (
            sugestoes.hash_preferencias != (preferencias.hash if preferencias else "")
        )
