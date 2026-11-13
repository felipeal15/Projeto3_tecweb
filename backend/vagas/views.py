from django.db.models import OuterRef, Subquery
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Analise, Vaga
from .serializers import VagaSerializer

STATUS_VALIDOS = [valor for valor, _ in Vaga.Status.choices]


def vagas_do_usuario(usuario):
    """Só as vagas do usuário logado, já com a nota da análise mais recente."""
    nota_mais_recente = (
        Analise.objects.filter(vaga=OuterRef("pk"))
        .order_by("-criado_em")
        .values("nota")[:1]
    )
    return Vaga.objects.filter(usuario=usuario).annotate(
        nota_mais_recente=Subquery(nota_mais_recente)
    )


@api_view(["GET", "POST"])
def api_vagas(request):
    if request.method == "POST":
        serializer = VagaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vaga = serializer.save(usuario=request.user)
        return Response(VagaSerializer(vaga).data, status=status.HTTP_201_CREATED)

    vagas = vagas_do_usuario(request.user)
    filtro = request.query_params.get("status")
    if filtro:
        if filtro not in STATUS_VALIDOS:
            return Response(
                {"detail": f"Status inválido. Use um destes: {', '.join(STATUS_VALIDOS)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vagas = vagas.filter(status=filtro)
    return Response(VagaSerializer(vagas, many=True).data)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def api_vaga(request, vaga_id):
    # Vaga de outro usuário responde 404, como se não existisse.
    try:
        vaga = vagas_do_usuario(request.user).get(id=vaga_id)
    except Vaga.DoesNotExist:
        raise Http404()

    if request.method == "DELETE":
        vaga.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method in ("PUT", "PATCH"):
        # PATCH muda só os campos enviados (ex.: {"status": "entrevista"} no kanban).
        serializer = VagaSerializer(
            vaga, data=request.data, partial=request.method == "PATCH"
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        vaga = vagas_do_usuario(request.user).get(id=vaga_id)

    return Response(VagaSerializer(vaga).data)
