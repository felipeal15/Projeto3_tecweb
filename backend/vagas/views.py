from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from contas.models import Preferencias
from contas.serializers import UsuarioSerializer

from . import ia, pdf, vagas_reais
from .compatibilidade import fora_das_preferencias, nome_da_cidade
from .models import Analise, Carta, Curriculo, Sugestoes, Vaga
from .serializers import (
    AnaliseSerializer,
    CartaSerializer,
    CurriculoSerializer,
    GerarCartaSerializer,
    ResultadoAnaliseSerializer,
    ResultadoCartaSerializer,
    ResultadoRankingSerializer,
    ResultadoSugestoesSerializer,
    SugestoesSerializer,
    VagaSerializer,
)


def preferencias_para_ia(preferencias):
    """O dict das preferências para o prompt, ou None se o usuário não preencheu nada."""
    return preferencias.para_ia() if preferencias else None

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
    contexto = {"preferencias": Preferencias.do_usuario(request.user)}
    if request.method == "POST":
        serializer = VagaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vaga = serializer.save(usuario=request.user)
        return Response(VagaSerializer(vaga, context=contexto).data, status=status.HTTP_201_CREATED)

    vagas = vagas_do_usuario(request.user)
    filtro = request.query_params.get("status")
    if filtro:
        if filtro not in STATUS_VALIDOS:
            return Response(
                {"detail": f"Status inválido. Use um destes: {', '.join(STATUS_VALIDOS)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vagas = vagas.filter(status=filtro)
    return Response(VagaSerializer(vagas, many=True, context=contexto).data)


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

    contexto = {"preferencias": Preferencias.do_usuario(request.user)}
    return Response(VagaSerializer(vaga, context=contexto).data)


def erro_da_ia(mensagem, codigo="formato_invalido"):
    """Falha da IA: 502 com a mensagem e o tipo do erro (ver ia.ErroIA)."""
    return Response(
        {"detail": str(mensagem), "codigo": codigo}, status=status.HTTP_502_BAD_GATEWAY
    )


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
        return erro_da_ia(
            f"Currículo salvo, mas a IA não conseguiu organizá-lo. {erro}", erro.codigo
        )
    return Response(CurriculoSerializer(curriculo).data)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def api_curriculo_pdf(request):
    """POST multipart {arquivo}: devolve o texto lido do PDF, sem salvar nada.

    Quem salva é o PUT /api/curriculo/, depois que o usuário confere o texto na tela.
    """
    arquivo = request.FILES.get("arquivo")
    if arquivo is None:
        # Mesmo formato {detail, codigo} dos erros do pdf.py, que a tela já sabe mostrar.
        return Response(
            {"detail": "Escolha o PDF do seu currículo.", "codigo": "sem_arquivo"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        lido = pdf.extrair_texto(arquivo)
    except pdf.ErroPdf as erro:
        return Response(
            {"detail": str(erro), "codigo": erro.codigo}, status=status.HTTP_400_BAD_REQUEST
        )
    return Response(lido)


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

    # Cache da análise: mesmo currículo + mesma vaga + mesmas preferências = mesma resposta.
    preferencias = Preferencias.do_usuario(request.user)
    hash_curriculo, hash_vaga = curriculo.hash_texto, vaga.hash_conteudo
    hash_pref = preferencias.hash if preferencias else ""
    analise = vaga.analises.filter(
        hash_curriculo=hash_curriculo, hash_vaga=hash_vaga, hash_preferencias=hash_pref
    ).first()
    if analise:
        return Response(AnaliseSerializer(analise).data)

    try:
        estruturar_se_preciso(curriculo)
        resposta = ia.analisar_vaga(
            curriculo.dados, vaga, preferencias=preferencias_para_ia(preferencias)
        )
    except ia.ErroIA as erro:
        return erro_da_ia(erro, erro.codigo)

    resultado = ResultadoAnaliseSerializer(data=resposta)
    if not resultado.is_valid():
        return erro_da_ia("A IA devolveu uma análise fora do formato esperado. Tente de novo.")

    analise = Analise.objects.create(
        vaga=vaga,
        curriculo=curriculo,
        hash_curriculo=hash_curriculo,
        hash_vaga=hash_vaga,
        hash_preferencias=hash_pref,
        nota=resultado.validated_data["nota"],
        resultado=resultado.validated_data,
        modelo_ia=settings.GEMINI_MODEL,
        versao_prompt=ia.VERSAO_PROMPT,
    )
    return Response(AnaliseSerializer(analise).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST", "PATCH"])
def api_carta(request, vaga_id):
    """GET: carta salva. POST {tom?, tamanho?}: a IA escreve (ou reescreve). PATCH {texto}: edição do usuário."""
    vaga = Vaga.objects.filter(usuario=request.user, id=vaga_id).first()
    if vaga is None:
        raise Http404()
    carta = Carta.objects.filter(vaga=vaga).first()

    if request.method == "GET":
        if carta is None:
            return Response({"detail": "Ainda não há carta para esta vaga."}, status=404)
        return Response(CartaSerializer(carta).data)

    if request.method == "PATCH":
        if carta is None:
            return Response({"detail": "Gere a carta antes de editar."}, status=404)
        serializer = CartaSerializer(carta, data={"texto": request.data.get("texto", "")}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # POST: sempre chama a IA, porque o usuário pediu uma versão nova.
    opcoes = GerarCartaSerializer(data=request.data)
    opcoes.is_valid(raise_exception=True)
    tom, tamanho = opcoes.validated_data["tom"], opcoes.validated_data["tamanho"]

    curriculo = Curriculo.objects.filter(usuario=request.user).first()
    if curriculo is None:
        return Response(
            {"detail": "Cadastre seu currículo antes de gerar a carta."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    hash_curriculo, hash_vaga = curriculo.hash_texto, vaga.hash_conteudo
    # Se a vaga já foi analisada com este currículo, as lacunas ajudam a carta a ser honesta.
    analise = vaga.analises.filter(hash_curriculo=hash_curriculo, hash_vaga=hash_vaga).first()
    nome = UsuarioSerializer(request.user).data["nome"]

    try:
        estruturar_se_preciso(curriculo)
        resposta = ia.escrever_carta(
            curriculo.dados,
            vaga,
            nome,
            tom,
            tamanho,
            analise.resultado if analise else None,
            preferencias=preferencias_para_ia(Preferencias.do_usuario(request.user)),
        )
    except ia.ErroIA as erro:
        return erro_da_ia(erro, erro.codigo)

    resultado = ResultadoCartaSerializer(data=resposta)
    if not resultado.is_valid():
        return erro_da_ia("A IA devolveu uma carta fora do formato esperado. Tente de novo.")

    texto = resultado.validated_data["carta"].strip()
    carta, _ = Carta.objects.update_or_create(
        vaga=vaga,
        defaults={
            "texto": texto,
            "texto_gerado": texto,
            "fatos_usados": resultado.validated_data["fatos_usados"],
            "tom": tom,
            "tamanho": tamanho,
            "hash_curriculo": hash_curriculo,
            "hash_vaga": hash_vaga,
            "modelo_ia": settings.GEMINI_MODEL,
            "versao_prompt": ia.VERSAO_PROMPT_CARTA,
        },
    )
    return Response(CartaSerializer(carta).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
def api_sugestoes(request):
    """GET: últimas sugestões de busca. POST: a IA gera sugestões novas (substitui as anteriores)."""
    preferencias = Preferencias.do_usuario(request.user)
    contexto = {"preferencias": preferencias}

    if request.method == "GET":
        sugestoes = Sugestoes.objects.filter(usuario=request.user).first()
        if sugestoes is None:
            return Response({"detail": "Você ainda não pediu sugestões de busca."}, status=404)
        return Response(SugestoesSerializer(sugestoes, context=contexto).data)

    curriculo = Curriculo.objects.filter(usuario=request.user).first()
    if curriculo is None:
        return Response(
            {"detail": "Cadastre seu currículo antes de pedir sugestões de busca."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        estruturar_se_preciso(curriculo)
        resposta = ia.sugerir_buscas(curriculo.dados, preferencias_para_ia(preferencias))
    except ia.ErroIA as erro:
        return erro_da_ia(erro, erro.codigo)

    resultado = ResultadoSugestoesSerializer(data=resposta)
    if not resultado.is_valid():
        return erro_da_ia("A IA devolveu sugestões fora do formato esperado. Tente de novo.")

    sugestoes, _ = Sugestoes.objects.update_or_create(
        usuario=request.user,
        defaults={
            "cargos": resultado.validated_data["cargos"],
            "hash_curriculo": curriculo.hash_texto,
            "hash_preferencias": preferencias.hash if preferencias else "",
            "modelo_ia": settings.GEMINI_MODEL,
            "versao_prompt": ia.VERSAO_PROMPT_SUGESTOES,
        },
    )
    return Response(
        SugestoesSerializer(sugestoes, context=contexto).data, status=status.HTTP_201_CREATED
    )


def termo_padrao(usuario, preferencias):
    """Busca de quem abre "Vagas para você" sem digitar nada: a melhor sugestão da IA ou a 1ª área."""
    sugestoes = Sugestoes.objects.filter(usuario=usuario).first()
    if sugestoes and sugestoes.cargos:
        return sugestoes.cargos[0]["busca"]
    if preferencias and preferencias.areas:
        nivel = {"estagio": "estágio", "trainee": "trainee", "junior": "júnior"}
        prefixo = nivel.get(preferencias.tipos[0], "") if preferencias.tipos else ""
        return f"{prefixo} {preferencias.areas[0]}".strip()
    return ""


@api_view(["GET"])
def api_vagas_reais(request):
    """GET ?q=termo: vagas reais do Adzuna, ranqueadas pela IA se o usuário tem currículo."""
    preferencias = Preferencias.do_usuario(request.user)
    termo = request.query_params.get("q", "").strip()[:80] or termo_padrao(request.user, preferencias)
    if not termo:
        return Response(
            {"detail": "Digite o que você procura (ex.: estágio dados)."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Mesma regra dos links de busca: quem só quer vaga remota não filtra por cidade.
    so_remoto = preferencias is not None and set(preferencias.modalidades) == {"remoto"}
    cidade = nome_da_cidade(preferencias.cidade) if preferencias and not so_remoto else ""

    try:
        vagas = vagas_reais.buscar(f"{termo} remoto" if so_remoto else termo, cidade)
    except vagas_reais.ErroVagas as erro:
        return erro_da_ia(erro, erro.codigo)

    # Vagas já salvas no kanban (pelo link) mostram "Salva" em vez do botão.
    salvas = dict(
        Vaga.objects.filter(usuario=request.user)
        .exclude(link="")
        .values_list("link", "id")
    )
    for vaga in vagas:
        vaga["salva_id"] = salvas.get(vaga["link"]) if vaga["link"] else None
        vaga["fora_das_preferencias"] = fora_das_preferencias(
            Vaga(titulo=vaga["titulo"], local=vaga["local"], descricao=vaga["descricao"]),
            preferencias,
        )
        vaga["nota"] = vaga["motivo"] = None

    resposta = {"termo": termo, "cidade": cidade, "vagas": vagas, "ranqueada": False, "erro_ranking": ""}
    curriculo = Curriculo.objects.filter(usuario=request.user).first()
    if not vagas or curriculo is None:
        return Response(resposta)

    # ponytail: uma chamada à IA por busca, sem cache; guardar o ranking por (currículo, ids) se a cota apertar.
    # Se a IA falhar, a lista volta sem notas em vez de dar erro.
    try:
        estruturar_se_preciso(curriculo)
        ranking = ResultadoRankingSerializer(
            data=ia.ranquear_vagas(curriculo.dados, vagas, preferencias_para_ia(preferencias))
        )
        if not ranking.is_valid():
            raise ia.ErroIA("A IA devolveu o ranking fora do formato esperado.", "formato_invalido")
    except ia.ErroIA as erro:
        resposta["erro_ranking"] = str(erro)
        return Response(resposta)

    notas = {item["id"]: item for item in ranking.validated_data["vagas"]}
    for vaga in vagas:
        if vaga["id"] in notas:
            vaga["nota"], vaga["motivo"] = notas[vaga["id"]]["nota"], notas[vaga["id"]]["motivo"]
    vagas.sort(key=lambda vaga: -1 if vaga["nota"] is None else vaga["nota"], reverse=True)
    resposta.update(
        ranqueada=True, modelo_ia=settings.GEMINI_MODEL, versao_prompt=ia.VERSAO_PROMPT_RANKING
    )
    return Response(resposta)
