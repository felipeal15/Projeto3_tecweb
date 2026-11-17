from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Preferencias
from .serializers import (
    CadastroSerializer,
    LoginSerializer,
    PreferenciasSerializer,
    UsuarioSerializer,
)


def resposta_com_token(usuario, codigo):
    token, _ = Token.objects.get_or_create(user=usuario)
    return Response(
        {"token": token.key, "usuario": UsuarioSerializer(usuario).data}, status=codigo
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def cadastro(request):
    serializer = CadastroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()
    return resposta_com_token(usuario, status.HTTP_201_CREATED)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return resposta_com_token(serializer.validated_data["usuario"], status.HTTP_200_OK)


@api_view(["POST"])
def logout(request):
    # Apagar o token invalida o login: a próxima requisição com ele recebe 401.
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def eu(request):
    """Devolve o usuário dono do token. O React usa para saber se ainda está logado."""
    return Response(UsuarioSerializer(request.user).data)


@api_view(["GET", "PUT"])
def preferencias(request):
    """GET: preferências do usuário (vazias, com atualizado_em null, se nunca salvou). PUT: salva."""
    atuais = Preferencias.do_usuario(request.user)

    if request.method == "GET":
        return Response(PreferenciasSerializer(atuais or Preferencias(usuario=request.user)).data)

    serializer = PreferenciasSerializer(atuais, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(usuario=request.user)
    return Response(serializer.data)
