import hashlib
import json

from django.conf import settings
from django.db import models


class Perfil(models.Model):
    """Dados do usuário que não cabem no User do Django.

    O login usa o User padrão (username = e-mail). As preferências de vaga
    ficam no modelo Preferencias, logo abaixo.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    nome = models.CharField(max_length=150)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Preferencias(models.Model):
    """O que o usuário procura numa vaga (uma linha por usuário).

    Entra no prompt da análise, da carta e das sugestões de busca, e no filtro do kanban.
    """

    class Tipo(models.TextChoices):
        ESTAGIO = "estagio", "Estágio"
        TRAINEE = "trainee", "Trainee"
        JUNIOR = "junior", "Júnior"

    class Modalidade(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        HIBRIDO = "hibrido", "Híbrido"
        REMOTO = "remoto", "Remoto"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferencias"
    )
    areas = models.JSONField(default=list, blank=True)  # ex.: ["Dados", "Desenvolvimento web"]
    tipos = models.JSONField(default=list, blank=True)  # valores de Tipo
    modalidades = models.JSONField(default=list, blank=True)  # valores de Modalidade
    cidade = models.CharField(max_length=120, blank=True)
    stack = models.JSONField(default=list, blank=True)  # ex.: ["Python", "SQL"]
    evitar = models.CharField("prefiro evitar", max_length=300, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    CAMPOS = ("areas", "tipos", "modalidades", "cidade", "stack", "evitar")

    class Meta:
        verbose_name_plural = "preferências"

    @classmethod
    def do_usuario(cls, usuario):
        """As preferências salvas do usuário (objeto ou id), ou None."""
        return cls.objects.filter(usuario=usuario).first()

    @property
    def vazia(self):
        return not any(getattr(self, campo) for campo in self.CAMPOS)

    @property
    def hash(self):
        """Chave de cache: muda quando muda alguma preferência ("" se nada foi preenchido)."""
        if self.vazia:
            return ""
        valores = {}
        for campo in self.CAMPOS:
            valor = getattr(self, campo)
            valores[campo] = sorted(valor) if isinstance(valor, list) else valor
        texto = json.dumps(valores, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def para_ia(self):
        """As preferências preenchidas, em português, para ir no prompt. None se estiver vazia."""
        tipos = dict(self.Tipo.choices)
        modalidades = dict(self.Modalidade.choices)
        dados = {
            "areas_de_interesse": self.areas,
            "tipos_de_vaga": [tipos.get(t, t) for t in self.tipos],
            "modalidades": [modalidades.get(m, m) for m in self.modalidades],
            "cidade": self.cidade,
            "stack_que_quer_usar": self.stack,
            "prefere_evitar": self.evitar,
        }
        dados = {chave: valor for chave, valor in dados.items() if valor}
        return dados or None

    def __str__(self):
        return f"Preferências de {self.usuario}"


def hash_preferencias(usuario):
    """Hash das preferências atuais do usuário (objeto ou id); "" se ele não tem nenhuma."""
    preferencias = Preferencias.do_usuario(usuario)
    return preferencias.hash if preferencias else ""
