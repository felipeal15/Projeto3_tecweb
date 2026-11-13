from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import ia
from .models import Analise, Curriculo, Vaga
from .serializers import (
    AnaliseSerializer,
    CurriculoSerializer,
    ResultadoAnaliseSerializer,
    VagaSerializer,
)

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


def erro_da_ia(erro):
    return Response({"detail": str(erro)}, status=status.HTTP_502_BAD_GATEWAY)


def estruturar_se_preciso(curriculo):
    """Cache do currículo: só chama a IA se o texto mudou desde a última estruturação."""
    if curriculo.dados is not None and curriculo.hash_dados == curriculo.hash_texto:
        return
    curriculo.dados = ia.estruturar_curriculo(curriculo.texto)
    curriculo.hash_dados = curriculo.hash_texto
    curriculo.save()


@api_view(["GET", "PUT"])
def api_curriculo(request):
    curriculo = Curriculo.objects.filter(usuario=request.user).first()

    if request.method == "GET":
        if curriculo is None:
            return Response({"detail": "Você ainda não cadastrou o currículo."}, status=404)
        return Response(CurriculoSerializer(curriculo).data)

    serializer = CurriculoSerializer(curriculo, data=request.data)
    serializer.is_valid(raise_exception=True)
    # O texto é salvo mesmo se a IA falhar; a estruturação é tentada de novo na análise.
    curriculo = serializer.save(usuario=request.user)
    try:
        estruturar_se_preciso(curriculo)
    except ia.ErroIA as erro:
        return erro_da_ia(f"Currículo salvo, mas a IA não conseguiu organizá-lo: {erro}")
    return Response(CurriculoSerializer(curriculo).data)


@api_view(["GET", "POST"])
def api_analise(request, vaga_id):
    vaga = Vaga.objects.filter(usuario=request.user, id=vaga_id).first()
    if vaga is None:
        raise Http404()

    if request.method == "GET":
        analise = vaga.analises.first()
        if analise is None:
            return Response({"detail": "Esta vaga ainda não foi analisada."}, status=404)
        return Response(AnaliseSerializer(analise).data)

    curriculo = Curriculo.objects.filter(usuario=request.user).first()
    if curriculo is None:
        return Response(
            {"detail": "Cadastre seu currículo antes de analisar uma vaga."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Cache da análise: mesmo currículo + mesma vaga = mesma resposta, sem chamar a IA.
    hash_curriculo, hash_vaga = curriculo.hash_texto, vaga.hash_conteudo
    analise = vaga.analises.filter(hash_curriculo=hash_curriculo, hash_vaga=hash_vaga).first()
    if analise:
        return Response(AnaliseSerializer(analise).data)

    try:
        estruturar_se_preciso(curriculo)
        resposta = ia.analisar_vaga(curriculo.dados, vaga)
    except ia.ErroIA as erro:
        return erro_da_ia(erro)

    resultado = ResultadoAnaliseSerializer(data=resposta)
    if not resultado.is_valid():
        return erro_da_ia("A IA devolveu uma análise fora do formato esperado. Tente de novo.")

    analise = Analise.objects.create(
        vaga=vaga,
        curriculo=curriculo,
        hash_curriculo=hash_curriculo,
        hash_vaga=hash_vaga,
        nota=resultado.validated_data["nota"],
        resultado=resultado.validated_data,
        modelo_ia=settings.GEMINI_MODEL,
        versao_prompt=ia.VERSAO_PROMPT,
    )
    return Response(AnaliseSerializer(analise).data, status=status.HTTP_201_CREATED)
