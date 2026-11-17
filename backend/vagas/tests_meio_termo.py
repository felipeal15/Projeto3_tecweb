"""Testes do meio-termo: preferências no filtro do kanban, na análise, na carta e nas sugestões de busca.

A IA é simulada (mock), como em tests.py: nenhum teste gasta a cota do Gemini.
"""

from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from contas.models import Perfil, Preferencias

from . import ia
from .busca import links_de_busca
from .compatibilidade import fora_das_preferencias
from .ia import ErroIA
from .models import Sugestoes, Vaga
from .tests import ANALISE, CARTA, CURRICULO, DADOS, VAGA

PREFERENCIAS = {
    "areas": ["Dados"],
    "tipos": ["estagio"],
    "modalidades": ["hibrido", "remoto"],
    "cidade": "São Paulo, SP",
    "stack": ["Python", "SQL"],
    "evitar": "Mais de 30 horas semanais",
}
SUGESTOES = {
    "cargos": [
        {"cargo": "Estágio em Desenvolvimento Web", "area": "Desenvolvimento web", "nota": 70,
         "por_que": "Projetos com Django.", "busca": "estágio desenvolvedor", "palavras_chave": ["django", "react"]},
        {"cargo": "Estágio em Dados", "area": "Dados", "nota": 85,
         "por_que": "Você tem Python e marcou Dados.", "busca": "estágio dados", "palavras_chave": ["python", "sql"]},
    ]
}


def vaga(titulo="Estágio em Dados", local="", descricao="Python e SQL."):
    return Vaga(titulo=titulo, empresa="ACME", local=local, descricao=descricao)


def preferencias(**campos):
    return Preferencias(**{"tipos": [], "modalidades": [], "cidade": "", **campos})


class CompatibilidadeTests(SimpleTestCase):
    """Filtro do kanban: só aponta conflito quando a vaga diz claramente outra coisa."""

    def test_sem_preferencias_nada_e_conflito(self):
        self.assertEqual(fora_das_preferencias(vaga("Desenvolvedor Júnior", "Presencial"), None), [])

    def test_tipo_de_vaga_pelo_cargo(self):
        so_estagio = preferencias(tipos=["estagio"])
        self.assertEqual(fora_das_preferencias(vaga("Desenvolvedor Júnior"), so_estagio), ["Júnior"])
        self.assertEqual(fora_das_preferencias(vaga("Analista Jr. de BI"), so_estagio), ["Júnior"])
        self.assertEqual(fora_das_preferencias(vaga("Programa de Trainee 2027"), so_estagio), ["Trainee"])
        self.assertEqual(fora_das_preferencias(vaga("Estagiário de Dados"), so_estagio), [])
        # Cargo sem nível: não dá para saber, então a vaga continua aparecendo.
        self.assertEqual(fora_das_preferencias(vaga("Analista de Dados"), so_estagio), [])

    def test_modalidade_pelo_local_ou_pela_descricao(self):
        hibrido_ou_remoto = preferencias(modalidades=["hibrido", "remoto"])
        self.assertEqual(
            fora_das_preferencias(vaga(local="Campinas · Presencial"), hibrido_ou_remoto), ["Presencial"]
        )
        self.assertEqual(
            fora_das_preferencias(vaga(descricao="Trabalho 100% presencial."), hibrido_ou_remoto),
            ["Presencial"],
        )
        # Híbrido com dias presenciais combina com quem aceita híbrido.
        self.assertEqual(
            fora_das_preferencias(vaga(descricao="Modelo híbrido: 3 dias presenciais."), hibrido_ou_remoto),
            [],
        )
        self.assertEqual(fora_das_preferencias(vaga(descricao="Python."), hibrido_ou_remoto), [])
        self.assertEqual(
            fora_das_preferencias(vaga(local="Home office"), preferencias(modalidades=["presencial"])),
            ["Remoto"],
        )

    def test_cidade(self):
        sao_paulo = preferencias(cidade="São Paulo, SP")
        self.assertEqual(
            fora_das_preferencias(vaga(local="Rio de Janeiro · Híbrido"), sao_paulo), ["Fora de São Paulo"]
        )
        self.assertEqual(fora_das_preferencias(vaga(local="Sao Paulo - SP"), sao_paulo), [])
        self.assertEqual(fora_das_preferencias(vaga(local="Remoto"), sao_paulo), [])  # vaga 100% remota
        self.assertEqual(fora_das_preferencias(vaga(local="Híbrido"), sao_paulo), [])  # local sem cidade
        self.assertEqual(fora_das_preferencias(vaga(local=""), sao_paulo), [])
        # Quem só quer remoto não liga para a cidade (a modalidade já aponta o conflito).
        so_remoto = preferencias(cidade="São Paulo", modalidades=["remoto"])
        self.assertEqual(fora_das_preferencias(vaga(local="Recife · Presencial"), so_remoto), ["Presencial"])

    def test_varios_conflitos_juntos(self):
        resultado = fora_das_preferencias(
            vaga("Desenvolvedor Júnior", "Belo Horizonte · Presencial"),
            preferencias(tipos=["estagio"], modalidades=["remoto", "hibrido"], cidade="São Paulo"),
        )
        self.assertEqual(resultado, ["Júnior", "Presencial", "Fora de São Paulo"])


class LinksDeBuscaTests(SimpleTestCase):
    def consulta(self, url):
        return {chave: valor[0] for chave, valor in parse_qs(urlparse(url).query).items()}

    def test_sem_preferencias(self):
        linkedin, gupy, indeed = links_de_busca("estágio dados")
        self.assertEqual(self.consulta(linkedin["url"]), {"keywords": "estágio dados", "location": "Brasil"})
        self.assertEqual(gupy["url"], "https://portal.gupy.io/job-search/term=est%C3%A1gio%20dados")
        self.assertEqual(self.consulta(indeed["url"]), {"q": "estágio dados"})
        self.assertEqual([link["site"] for link in (linkedin, gupy, indeed)], ["LinkedIn", "Gupy", "Indeed"])

    def test_com_cidade_modalidade_e_nivel(self):
        linkedin, _, indeed = links_de_busca(
            "estágio dados", preferencias(tipos=["estagio", "junior"], modalidades=["hibrido", "remoto"], cidade="São Paulo, SP")
        )
        self.assertEqual(
            self.consulta(linkedin["url"]),
            {"keywords": "estágio dados", "location": "São Paulo", "f_WT": "2,3", "f_E": "1,2"},
        )
        self.assertEqual(self.consulta(indeed["url"]), {"q": "estágio dados", "l": "São Paulo"})

    def test_so_remoto_ignora_a_cidade(self):
        linkedin, _, indeed = links_de_busca("dev web", preferencias(modalidades=["remoto"], cidade="Recife"))
        self.assertEqual(self.consulta(linkedin["url"])["location"], "Brasil")
        self.assertEqual(self.consulta(linkedin["url"])["f_WT"], "2")
        self.assertEqual(self.consulta(indeed["url"]), {"q": "dev web remoto"})


class PromptsTests(SimpleTestCase):
    """O que vai no texto enviado ao Gemini (sem chamar a API)."""

    def prompt(self, chamar):
        return chamar.call_args.args[0]

    @patch("vagas.ia.chamar_gemini", return_value=ANALISE)
    def test_analise_com_e_sem_preferencias(self, chamar):
        ia.analisar_vaga(DADOS, vaga(), preferencias={"cidade": "Recife", "prefere_evitar": "Plantão"})
        prompt = self.prompt(chamar)
        self.assertIn("PREFERÊNCIAS DO CANDIDATO", prompt)
        self.assertIn("Recife", prompt)
        self.assertIn("Plantão", prompt)
        self.assertIn("não mudam a nota", prompt)

        ia.analisar_vaga(DADOS, vaga())
        self.assertNotIn("PREFERÊNCIAS DO CANDIDATO", self.prompt(chamar))
        self.assertIn("alertas_preferencias: lista vazia", self.prompt(chamar))

    @patch("vagas.ia.chamar_gemini", return_value=CARTA)
    def test_carta_usa_so_areas_e_stack(self, chamar):
        ia.escrever_carta(
            DADOS, vaga(), "Maria", "neutro", "curta",
            preferencias={"areas_de_interesse": ["Dados"], "stack_que_quer_usar": ["SQL"],
                          "cidade": "Recife", "prefere_evitar": "Plantão"},
        )
        prompt = self.prompt(chamar)
        self.assertIn("INTERESSES QUE O CANDIDATO MARCOU", prompt)
        self.assertIn("stack_que_quer_usar", prompt)
        self.assertNotIn("Recife", prompt)
        self.assertNotIn("Plantão", prompt)

    @patch("vagas.ia.chamar_gemini", return_value=SUGESTOES)
    def test_sugestoes(self, chamar):
        ia.sugerir_buscas(DADOS, {"areas_de_interesse": ["Dados"]})
        self.assertIn("PREFERÊNCIAS DO CANDIDATO", self.prompt(chamar))
        self.assertIs(chamar.call_args.args[1], ia.SCHEMA_SUGESTOES)
        ia.sugerir_buscas(DADOS)
        self.assertIn("não informou preferências", self.prompt(chamar))


# Chave vazia: se algum mock faltar, a chamada falha na hora em vez de ir ao Gemini de verdade.
@override_settings(GEMINI_API_KEY="")
class ComUsuario(APITestCase):
    def setUp(self):
        self.maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        Perfil.objects.create(usuario=self.maria, nome="Maria Silva")
        self.client.force_authenticate(self.maria)

    def salvar_preferencias(self, **campos):
        resposta = self.client.put("/api/preferencias/", {**PREFERENCIAS, **campos}, format="json")
        self.assertEqual(resposta.status_code, 200)


class KanbanComPreferenciasTests(ComUsuario):
    def test_cada_vaga_diz_o_que_vai_contra_as_preferencias(self):
        self.client.post("/api/vagas/", {**VAGA, "titulo": "Estágio em Dados", "local": "São Paulo · Híbrido"})
        self.client.post("/api/vagas/", {**VAGA, "titulo": "Desenvolvedor Júnior", "local": "Curitiba · Presencial"})
        # Sem preferências, nada fica de fora.
        self.assertEqual([v["fora_das_preferencias"] for v in self.client.get("/api/vagas/").data], [[], []])

        self.salvar_preferencias()
        vagas = {v["titulo"]: v["fora_das_preferencias"] for v in self.client.get("/api/vagas/").data}
        self.assertEqual(vagas["Estágio em Dados"], [])
        self.assertEqual(vagas["Desenvolvedor Júnior"], ["Júnior", "Presencial", "Fora de São Paulo"])
        id_junior = Vaga.objects.get(titulo="Desenvolvedor Júnior").id
        self.assertEqual(len(self.client.get(f"/api/vagas/{id_junior}/").data["fora_das_preferencias"]), 3)


@patch("vagas.ia.analisar_vaga", return_value={**ANALISE, "alertas_preferencias": ["É presencial."]})
@patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
class AnaliseComPreferenciasTests(ComUsuario):
    def setUp(self):
        super().setUp()
        # O @patch da classe não vale no setUp: o mock do currículo precisa ser feito aqui também.
        with patch("vagas.ia.estruturar_curriculo", return_value=DADOS):
            self.assertEqual(self.client.put("/api/curriculo/", {"texto": CURRICULO}).status_code, 200)
        self.url = f"/api/vagas/{self.client.post('/api/vagas/', VAGA).data['id']}/analise/"

    def test_preferencias_vao_para_a_ia_e_mudar_invalida_o_cache(self, estruturar, analisar):
        self.assertEqual(self.client.post(self.url).status_code, 201)
        self.assertIsNone(analisar.call_args.kwargs["preferencias"])

        self.salvar_preferencias()
        self.assertTrue(self.client.get(self.url).data["desatualizada"])

        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 201)  # nova chamada à IA
        self.assertEqual(analisar.call_count, 2)
        enviadas = analisar.call_args.kwargs["preferencias"]
        self.assertEqual(enviadas["tipos_de_vaga"], ["Estágio"])
        self.assertEqual(enviadas["prefere_evitar"], "Mais de 30 horas semanais")
        self.assertEqual(resposta.data["resultado"]["alertas_preferencias"], ["É presencial."])
        self.assertEqual(resposta.data["versao_prompt"], "v2")
        self.assertFalse(resposta.data["desatualizada"])

        # Mesmas preferências: volta do cache.
        self.assertEqual(self.client.post(self.url).status_code, 200)
        self.assertEqual(analisar.call_count, 2)

    def test_resposta_sem_alertas_vira_lista_vazia(self, estruturar, analisar):
        analisar.return_value = ANALISE  # sem o campo alertas_preferencias
        self.assertEqual(self.client.post(self.url).data["resultado"]["alertas_preferencias"], [])


@patch("vagas.ia.escrever_carta", return_value=CARTA)
@patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
class CartaComPreferenciasTests(ComUsuario):
    def test_carta_recebe_as_preferencias(self, estruturar, escrever):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.salvar_preferencias()
        url = f"/api/vagas/{self.client.post('/api/vagas/', VAGA).data['id']}/carta/"
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["versao_prompt"], "carta-v2")
        self.assertEqual(escrever.call_args.kwargs["preferencias"]["areas_de_interesse"], ["Dados"])
        self.assertEqual(len(escrever.call_args.args), 6)  # o resto da chamada não mudou


@patch("vagas.ia.sugerir_buscas", return_value=SUGESTOES)
@patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
class SugestoesTests(ComUsuario):
    URL = "/api/sugestoes/"

    def test_precisa_de_curriculo(self, estruturar, sugerir):
        self.assertEqual(self.client.get(self.URL).status_code, 404)
        self.assertEqual(self.client.post(self.URL).status_code, 400)
        sugerir.assert_not_called()

    def test_gera_ordena_e_monta_os_links(self, estruturar, sugerir):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.salvar_preferencias()
        resposta = self.client.post(self.URL)
        self.assertEqual(resposta.status_code, 201)
        cargos = resposta.data["cargos"]
        self.assertEqual([c["cargo"] for c in cargos], ["Estágio em Dados", "Estágio em Desenvolvimento Web"])
        self.assertEqual([link["site"] for link in cargos[0]["links"]], ["LinkedIn", "Gupy", "Indeed"])
        self.assertIn("location=S%C3%A3o+Paulo", cargos[0]["links"][0]["url"])
        self.assertFalse(resposta.data["desatualizada"])
        self.assertEqual(resposta.data["versao_prompt"], "sugestoes-v1")
        self.assertEqual(sugerir.call_args.args[1]["areas_de_interesse"], ["Dados"])
        self.assertEqual(self.client.get(self.URL).data["cargos"], cargos)

    def test_mudar_preferencias_avisa_e_atualiza_os_links_sem_chamar_a_ia(self, estruturar, sugerir):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.salvar_preferencias()
        self.client.post(self.URL)
        self.salvar_preferencias(cidade="Recife", modalidades=["presencial"])
        resposta = self.client.get(self.URL)
        self.assertTrue(resposta.data["desatualizada"])
        self.assertIn("location=Recife", resposta.data["cargos"][0]["links"][0]["url"])
        self.assertEqual(sugerir.call_count, 1)

        # Atualizar: substitui as anteriores.
        self.client.post(self.URL)
        self.assertEqual(Sugestoes.objects.count(), 1)
        self.assertFalse(self.client.get(self.URL).data["desatualizada"])

    def test_resposta_invalida_ou_erro_da_ia_nao_salvam(self, estruturar, sugerir):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        sugerir.return_value = {"cargos": []}
        self.assertEqual(self.client.post(self.URL).status_code, 502)
        sugerir.return_value = {"cargos": [{**SUGESTOES["cargos"][0], "nota": 150}]}
        self.assertEqual(self.client.post(self.URL).status_code, 502)
        sugerir.side_effect = ErroIA("Limite", "limite")
        resposta = self.client.post(self.URL)
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(resposta.data["codigo"], "limite")
        self.assertEqual(self.client.get(self.URL).status_code, 404)

    def test_cada_usuario_ve_so_as_suas(self, estruturar, sugerir):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.client.post(self.URL)
        self.client.force_authenticate(User.objects.create_user("joao@x.com", "joao@x.com", "senha"))
        self.assertEqual(self.client.get(self.URL).status_code, 404)
