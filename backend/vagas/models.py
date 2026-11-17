import hashlib

from django.conf import settings
from django.db import models


def gerar_hash(texto):
    """SHA-256 de um texto. Serve de chave de cache: texto igual, hash igual."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class Curriculo(models.Model):
    """O currículo do usuário (um por usuário), colado como texto."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="curriculo"
    )
    texto = models.TextField()
    # Currículo estruturado pela IA (formação, experiências, habilidades...).
    dados = models.JSONField(null=True, blank=True)
    # Hash do texto que gerou `dados`. Se for diferente de `hash_texto`,
    # o texto mudou depois da estruturação e `dados` está desatualizado.
    hash_dados = models.CharField(max_length=64, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    @property
    def hash_texto(self):
        return gerar_hash(self.texto)

    def __str__(self):
        return f"Currículo de {self.usuario}"


class Vaga(models.Model):
    """Uma vaga que o usuário salvou e acompanha no kanban."""

    class Status(models.TextChoices):
        INTERESSADO = "interessado", "Interessado"
        CANDIDATADO = "candidatado", "Candidatado"
        ENTREVISTA = "entrevista", "Entrevista"
        OFERTA = "oferta", "Oferta"
        ENCERRADA = "encerrada", "Encerrada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vagas"
    )
    titulo = models.CharField("cargo", max_length=200)
    empresa = models.CharField(max_length=200)
    local = models.CharField(max_length=120, blank=True)  # ex.: "São Paulo", "Remoto"
    link = models.URLField(max_length=500, blank=True)
    descricao = models.TextField("descrição")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INTERESSADO
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-atualizado_em"]

    @property
    def hash_conteudo(self):
        """Muda quando muda o que a IA lê da vaga (cargo, empresa ou descrição)."""
        return gerar_hash(f"{self.titulo}\n{self.empresa}\n{self.descricao}")

    def __str__(self):
        return f"{self.titulo} · {self.empresa}"


class Analise(models.Model):
    """Resultado da IA comparando um currículo com uma vaga.

    Os hashes do currículo, da vaga e das preferências são a chave do cache: se já
    existe uma análise com os três hashes atuais, não precisa chamar a IA.
    """

    vaga = models.ForeignKey(Vaga, on_delete=models.CASCADE, related_name="analises")
    curriculo = models.ForeignKey(
        Curriculo, on_delete=models.CASCADE, related_name="analises"
    )
    hash_curriculo = models.CharField(max_length=64)
    hash_vaga = models.CharField(max_length=64)
    # "" = feita sem preferências (ver contas.models.hash_preferencias).
    hash_preferencias = models.CharField(max_length=64, blank=True, default="")
    nota = models.PositiveSmallIntegerField()  # aderência de 0 a 100
    # Requisitos atendidos, lacunas, sugestões... no formato do schema da IA.
    resultado = models.JSONField(default=dict)
    modelo_ia = models.CharField(max_length=60, blank=True)
    versao_prompt = models.CharField(max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["vaga", "hash_curriculo", "hash_vaga"])]

    def __str__(self):
        return f"Análise de {self.vaga} ({self.nota}%)"


class Carta(models.Model):
    """Carta de apresentação de uma vaga (uma por vaga).

    A IA escreve o rascunho e o usuário pode editar. "Gerar outra versão"
    substitui o texto. `texto_gerado` guarda o que a IA escreveu, para saber
    se o usuário mexeu.
    """

    class Tom(models.TextChoices):
        FORMAL = "formal", "Formal"
        NEUTRO = "neutro", "Neutro"
        ENTUSIASMADO = "entusiasmado", "Entusiasmado"

    class Tamanho(models.TextChoices):
        CURTA = "curta", "Curta"
        MEDIA = "media", "Média"

    vaga = models.OneToOneField(Vaga, on_delete=models.CASCADE, related_name="carta")
    texto = models.TextField()
    texto_gerado = models.TextField()
    # Fatos do currículo que a IA diz ter usado, para o usuário conferir.
    fatos_usados = models.JSONField(default=list)
    tom = models.CharField(max_length=20, choices=Tom.choices, default=Tom.NEUTRO)
    tamanho = models.CharField(max_length=10, choices=Tamanho.choices, default=Tamanho.CURTA)
    # Hashes do currículo e da vaga usados na geração (para avisar se mudaram).
    hash_curriculo = models.CharField(max_length=64)
    hash_vaga = models.CharField(max_length=64)
    modelo_ia = models.CharField(max_length=60, blank=True)
    versao_prompt = models.CharField(max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carta para {self.vaga}"


class Sugestoes(models.Model):
    """Cargos e palavras-chave de busca que a IA sugeriu para o usuário (uma linha por usuário).

    "Atualizar sugestões" substitui o conteúdo. Os hashes avisam se o currículo
    ou as preferências mudaram depois.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sugestoes"
    )
    # [{cargo, area, nota, por_que, busca, palavras_chave[]}], da maior para a menor nota.
    cargos = models.JSONField(default=list)
    hash_curriculo = models.CharField(max_length=64)
    hash_preferencias = models.CharField(max_length=64, blank=True, default="")
    modelo_ia = models.CharField(max_length=60, blank=True)
    versao_prompt = models.CharField(max_length=20, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "sugestões"

    def __str__(self):
        return f"Sugestões de busca de {self.usuario}"
