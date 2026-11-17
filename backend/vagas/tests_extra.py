"""Testes do extra: vagas reais do Adzuna, ranking da IA e "salvar no kanban".

A API do Adzuna e a IA são simuladas (mock): nenhum teste sai para a internet.
"""

import io
import json
import urllib.error
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from contas.models import Preferencias

from . import vagas_reais
from .ia import ErroIA
from .models import Curriculo, Sugestoes, Vaga, gerar_hash
from .tests import CURRICULO, DADOS

ITEM_ADZUNA = {
    "id": 4123,
    "title": "Estágio em <strong>Dados</strong> &amp; BI",
    "company": {"display_name": "ACME"},
    "location": {"display_name": "São Paulo, SP"},
    "description": "Python, SQL e   Power BI. Trabalho presencial.",
    "redirect_url": "https://www.adzuna.com.br/land/ad/4123",
    "created": "2026-11-10T12:00:00Z",
}


def vaga_real(id_, titulo="Estágio em Dados", local="São Paulo", link=None, descricao="Python e SQL."):
    return {
        "id": id_, "titulo": titulo, "empresa": "ACME", "local": local, "descricao": descricao,
        "link": f"https://adzuna.com.br/{id_}" if link is None else link, "criado_em": None,
    }


class AdzunaTests(SimpleTestCase):
    def test_normaliza_no_formato_da_vaga(self):
        vaga = vagas_reais.normalizar(ITEM_ADZUNA)
        self.assertEqual(vaga["id"], "4123")
        self.assertEqual(vaga["titulo"], "Estágio em Dados & BI")  # sem <strong> e sem &amp;
        self.assertEqual(vaga["descricao"], "Python, SQL e Power BI. Trabalho presencial.")
        self.assertEqual(vaga["local"], "São Paulo, SP")
        semi_vazia = vagas_reais.normalizar({"id": 1, "title": "X", "redirect_url": "https://a.com/" + "x" * 600})
        self.assertEqual(semi_vazia["empresa"], "Empresa não informada")
        self.assertEqual(semi_vazia["link"], "")  # link maior que Vaga.link: melhor sem link que quebrado

    @override_settings(ADZUNA_APP_ID="", ADZUNA_APP_KEY="")
    def test_sem_chave(self):
        with self.assertRaises(vagas_reais.ErroVagas) as erro:
            vagas_reais.buscar("estágio dados")
        self.assertEqual(erro.exception.codigo, "sem_chave")

    @override_settings(ADZUNA_APP_ID="id", ADZUNA_APP_KEY="chave")
    def test_busca_no_brasil_com_cidade(self):
        resposta = io.BytesIO(json.dumps({"results": [ITEM_ADZUNA]}).encode())
        with patch("urllib.request.urlopen", return_value=resposta) as urlopen:
            vagas = vagas_reais.buscar("estágio dados", "São Paulo")
        url = urlparse(urlopen.call_args.args[0])
        self.assertIn("/jobs/br/search/", url.path)
        parametros = parse_qs(url.query)
        self.assertEqual(parametros["what"], ["estágio dados"])
        self.assertEqual(parametros["where"], ["São Paulo"])
        self.assertEqual([v["id"] for v in vagas], ["4123"])

    @override_settings(ADZUNA_APP_ID="id", ADZUNA_APP_KEY="chave")
    def test_erros_da_api(self):
        casos = [
            (urllib.error.HTTPError("u", 429, "", {}, None), "limite"),
            (urllib.error.HTTPError("u", 500, "", {}, None), "indisponivel"),
            (urllib.error.URLError("sem rede"), "sem_conexao"),
        ]
        for excecao, codigo in casos:
            with patch("urllib.request.urlopen", side_effect=excecao), self.assertRaises(
                vagas_reais.ErroVagas
            ) as erro:
                vagas_reais.buscar("dados")
            self.assertEqual(erro.exception.codigo, codigo)


@patch("vagas.views.vagas_reais.buscar")
class VagasReaisApiTests(APITestCase):
    def setUp(self):
        self.maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        self.client.force_authenticate(self.maria)

    def com_curriculo(self):
        # Já estruturado (hash_dados = hash do texto), para não chamar a IA de verdade.
        Curriculo.objects.create(
            usuario=self.maria, texto=CURRICULO, dados=DADOS, hash_dados=gerar_hash(CURRICULO)
        )

    def test_sem_termo_e_sem_sugestoes_pede_o_termo(self, buscar):
        self.assertEqual(self.client.get("/api/vagas-reais/").status_code, 400)
        buscar.assert_not_called()

    def test_termo_padrao_vem_da_melhor_sugestao_ou_das_preferencias(self, buscar):
        buscar.return_value = []
        Preferencias.objects.create(usuario=self.maria, areas=["Dados"], tipos=["estagio"])
        self.assertEqual(self.client.get("/api/vagas-reais/").data["termo"], "estágio Dados")
        Sugestoes.objects.create(
            usuario=self.maria, hash_curriculo="x",
            cargos=[{"cargo": "Estágio em BI", "busca": "estágio bi", "nota": 80}],
        )
        self.assertEqual(self.client.get("/api/vagas-reais/").data["termo"], "estágio bi")

    def test_cidade_das_preferencias_e_so_remoto(self, buscar):
        buscar.return_value = []
        prefs = Preferencias.objects.create(usuario=self.maria, cidade="Campinas, SP", modalidades=["hibrido"])
        self.client.get("/api/vagas-reais/?q=dados")
        buscar.assert_called_with("dados", "Campinas")
        prefs.modalidades = ["remoto"]
        prefs.save()
        self.client.get("/api/vagas-reais/?q=dados")
        buscar.assert_called_with("dados remoto", "")

    def test_sem_curriculo_lista_sem_ranking(self, buscar):
        buscar.return_value = [vaga_real("1")]
        with patch("vagas.views.ia.ranquear_vagas") as ranquear:
            dados = self.client.get("/api/vagas-reais/?q=dados").data
        ranquear.assert_not_called()
        self.assertFalse(dados["ranqueada"])
        self.assertIsNone(dados["vagas"][0]["nota"])

    def test_ranqueia_marca_salvas_e_conflitos(self, buscar):
        self.com_curriculo()
        Preferencias.objects.create(usuario=self.maria, tipos=["estagio"])
        Vaga.objects.create(usuario=self.maria, titulo="X", empresa="ACME", descricao="d", link="https://adzuna.com.br/2")
        buscar.return_value = [vaga_real("1"), vaga_real("2", titulo="Desenvolvedor Júnior"), vaga_real("3")]
        ranking = {"vagas": [
            {"id": "1", "nota": 40, "motivo": "Falta SQL."},
            {"id": "2", "nota": 90, "motivo": "Pede Python."},
            {"id": "99", "nota": 100, "motivo": "id inventado pela IA"},
        ]}
        with patch("vagas.views.ia.ranquear_vagas", return_value=ranking):
            dados = self.client.get("/api/vagas-reais/?q=dados").data
        self.assertTrue(dados["ranqueada"])
        # Maior nota primeiro; a vaga que a IA esqueceu fica no fim, sem nota.
        self.assertEqual([(v["id"], v["nota"]) for v in dados["vagas"]], [("2", 90), ("1", 40), ("3", None)])
        self.assertEqual(dados["vagas"][0]["fora_das_preferencias"], ["Júnior"])
        salva = Vaga.objects.get(link="https://adzuna.com.br/2")
        self.assertEqual([v["salva_id"] for v in dados["vagas"]], [salva.id, None, None])

    def test_falha_da_ia_devolve_a_lista_sem_notas(self, buscar):
        self.com_curriculo()
        buscar.return_value = [vaga_real("1")]
        for efeito in (ErroIA("Limite", "limite"), lambda *a, **k: {"vagas": [{"id": "1", "nota": 300}]}):
            with patch("vagas.views.ia.ranquear_vagas", side_effect=efeito):
                resposta = self.client.get("/api/vagas-reais/?q=dados")
            self.assertEqual(resposta.status_code, 200)
            self.assertFalse(resposta.data["ranqueada"])
            self.assertTrue(resposta.data["erro_ranking"])
            self.assertEqual(len(resposta.data["vagas"]), 1)

    def test_falha_do_adzuna_responde_502(self, buscar):
        buscar.side_effect = vagas_reais.ErroVagas("Sem chave.", "sem_chave")
        resposta = self.client.get("/api/vagas-reais/?q=dados")
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(resposta.data["codigo"], "sem_chave")

    def test_salvar_no_kanban_usa_o_crud_de_vagas(self, buscar):
        # O botão do frontend manda os campos da vaga real direto para POST /api/vagas/.
        vaga = vagas_reais.normalizar(ITEM_ADZUNA)
        campos = {chave: vaga[chave] for chave in ("titulo", "empresa", "local", "descricao", "link")}
        resposta = self.client.post("/api/vagas/", campos)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["status"], "interessado")


class CompararPromptsTests(SimpleTestCase):
    """O comando do diferencial roda os pares nas duas versões e calcula as métricas (IA simulada)."""

    def test_metricas_e_arquivo(self):
        import tempfile
        from pathlib import Path

        from django.core.management import call_command

        from .management.commands.comparar_prompts import metricas

        linhas = [
            {"referencia": 80, "v2": [70, 90], "v3": [80, 80]},
            {"referencia": 30, "v2": [60, None], "v3": [35, 25]},
        ]
        self.assertEqual(
            metricas(linhas, "v2"), {"erro_medio": 15, "acerto_faixa": "1/2", "variacao_media": 20, "falhas": 1}
        )
        self.assertEqual(metricas(linhas, "v3")["acerto_faixa"], "2/2")

        notas = {"v2": 50, "v3": 85}
        analise = lambda dados, vaga, versao: {  # noqa: E731
            "nota": notas[versao], "resumo": "r", "requisitos_atendidos": [], "lacunas": [], "sugestoes": [],
        }
        with tempfile.TemporaryDirectory() as pasta, patch("vagas.ia.analisar_vaga", side_effect=analise) as chamada:
            saida = Path(pasta) / "resultado.md"
            call_command("comparar_prompts", "--rodadas", "1", "--pausa", "0", "--saida", str(saida), stdout=io.StringIO())
            texto = saida.read_text(encoding="utf-8")
        self.assertEqual(chamada.call_count, 22)  # 11 pares x 2 versões
        self.assertIn("| v3 |", texto)
