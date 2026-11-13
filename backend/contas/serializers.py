from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Perfil

User = get_user_model()


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
