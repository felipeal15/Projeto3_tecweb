from django.conf import settings
from django.db import models


class Perfil(models.Model):
    """Dados do usuário que não cabem no User do Django.

    O login usa o User padrão (username = e-mail). As preferências da Sprint 2
    (áreas, modalidade, cidade, stack...) entram aqui ou num modelo ligado a ele.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    nome = models.CharField(max_length=150)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
