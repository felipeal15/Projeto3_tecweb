from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Perfil, Preferencias

User = get_user_model()


class ListaDeTextos(serializers.ListField):
    """Lista de textos curtos (áreas, stack): tira espaços, vazios e repetidos."""

    def __init__(self, tamanho_item=40, **kwargs):
        self.tamanho_item = tamanho_item
        super().__init__(child=serializers.CharField(allow_blank=True), **kwargs)

    def to_internal_value(self, data):
        limpos, vistos = [], set()
        for item in super().to_internal_value(data):
            item = " ".join(item.split())
            if len(item) > self.tamanho_item:
                raise serializers.ValidationError(
                    f"Cada item pode ter no máximo {self.tamanho_item} caracteres."
                )
            # "python" e "Python" contam como o mesmo item.
            if item and item.casefold() not in vistos:
                vistos.add(item.casefold())
                limpos.append(item)
        return limpos


class PreferenciasSerializer(serializers.ModelSerializer):
    areas = ListaDeTextos(max_length=10, required=False)
    stack = ListaDeTextos(max_length=15, required=False)
    tipos = serializers.ListField(
        child=serializers.ChoiceField(choices=Preferencias.Tipo.choices), required=False
    )
    modalidades = serializers.ListField(
        child=serializers.ChoiceField(choices=Preferencias.Modalidade.choices), required=False
    )

    class Meta:
        model = Preferencias
        fields = ["areas", "tipos", "modalidades", "cidade", "stack", "evitar", "atualizado_em"]
        # atualizado_em = null: o usuário nunca salvou (a tela mostra o passo 3 do onboarding).
        read_only_fields = ["atualizado_em"]

    def validate_tipos(self, tipos):
        return list(dict.fromkeys(tipos))  # tira repetidos mantendo a ordem

    def validate_modalidades(self, modalidades):
        return list(dict.fromkeys(modalidades))


class UsuarioSerializer(serializers.ModelSerializer):
    """O que o frontend recebe sobre o usuário logado."""

    nome = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "nome", "email"]

    def get_nome(self, usuario):
        perfil = Perfil.objects.filter(usuario=usuario).first()
        if perfil:
            return perfil.nome
        # Usuários criados pelo createsuperuser não têm Perfil.
        return usuario.get_full_name() or usuario.username


class CadastroSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, valor):
        email = valor.strip().lower()
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def validate(self, dados):
        # Usa os validadores do settings.py (mínimo de 8 caracteres, senha comum,
        # só números, parecida com o nome/e-mail). As mensagens saem em português.
        usuario_provisorio = User(username=dados["email"], email=dados["email"])
        try:
            validate_password(dados["senha"], user=usuario_provisorio)
        except DjangoValidationError as erro:
            raise serializers.ValidationError({"senha": list(erro.messages)})
        return dados

    def create(self, dados):
        # O e-mail também é o username, porque o login é feito por e-mail.
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=dados["email"], email=dados["email"], password=dados["senha"]
            )
            Perfil.objects.create(usuario=usuario, nome=dados["nome"].strip())
        return usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, dados):
        usuario = authenticate(
            username=dados["email"].strip().lower(), password=dados["senha"]
        )
        if usuario is None:
            raise serializers.ValidationError("E-mail ou senha incorretos.")
        dados["usuario"] = usuario
        return dados
