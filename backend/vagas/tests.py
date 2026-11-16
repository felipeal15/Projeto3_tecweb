import io
import json
import urllib.error
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from contas.models import Perfil

from . import ia
from .ia import ErroIA

CURRICULO = "Maria Silva. Engenharia de Computação no Insper (2023-2027). Python, Django, React."
DADOS = {"resumo": "Estudante", "formacao": [], "experiencias": [], "habilidades": ["Python"], "idiomas": [], "projetos": []}
ANALISE = {"nota": 72, "resumo": "Vale tentar.", "requisitos_atendidos": ["Python"], "lacunas": ["SQL"], "sugestoes": ["Estudar SQL"]}
CARTA = {
    "carta": "Olá, equipe da ACME,\n\nSou estudante de Engenharia de Computação no Insper e uso Python "
    "e Django nos meus projetos. Quero contribuir com o time e aprender SQL no dia a dia.\n\nAtenciosamente,\nMaria Silva",
    "fatos_usados": ["Engenharia de Computação · Insper (2023–2027)", "Habilidades: Python"],
}
VAGA = {"titulo": "Estágio Dev", "empresa": "ACME", "descricao": "Python e SQL"}


class VagasTests(APITestCase):
    """CRUD de vagas e o status do kanban."""

    def setUp(self):
        self.maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        self.client.force_authenticate(self.maria)

    def criar(self, **dados):
        return self.client.post("/api/vagas/", {**VAGA, **dados})

    def test_cria_vaga_com_status_padrao(self):
        resposta = self.criar(local="Remoto", link="https://acme.com/vaga")
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["status"], "interessado")
        self.assertIsNone(resposta.data["ultima_nota"])
        self.assertEqual(resposta.data["local"], "Remoto")

    def test_campos_obrigatorios_e_link_invalido(self):
        resposta = self.client.post("/api/vagas/", {})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(set(resposta.data), {"titulo", "empresa", "descricao"})
        self.assertEqual(self.criar(link="acme").status_code, 400)
        self.assertEqual(self.criar(status="sonhando").status_code, 400)

    def test_lista_e_filtra_por_status(self):
        self.criar(titulo="A")
        self.criar(titulo="B", status="entrevista")
        self.assertEqual(len(self.client.get("/api/vagas/").data), 2)
        filtradas = self.client.get("/api/vagas/?status=entrevista").data
        self.assertEqual([v["titulo"] for v in filtradas], ["B"])
        self.assertEqual(self.client.get("/api/vagas/?status=xyz").status_code, 400)

    def test_mover_no_kanban_editar_e_apagar(self):
        url = f"/api/vagas/{self.criar().data['id']}/"
        resposta = self.client.patch(url, {"status": "candidatado"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["status"], "candidatado")
        self.assertEqual(resposta.data["titulo"], "Estágio Dev")  # PATCH não mexe no resto
        self.assertEqual(self.client.patch(url, {"status": "xyz"}).status_code, 400)

        resposta = self.client.put(url, {**VAGA, "titulo": "Estágio Back-end"})
        self.assertEqual(resposta.data["titulo"], "Estágio Back-end")

        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_vaga_de_outro_usuario_responde_404(self):
        url = f"/api/vagas/{self.criar().data['id']}/"
        joao = User.objects.create_user("joao@x.com", "joao@x.com", "senha")
        self.client.force_authenticate(joao)
        self.assertEqual(self.client.get("/api/vagas/").data, [])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {"status": "oferta"}).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(self.client.post(url + "analise/").status_code, 404)
        self.assertEqual(self.client.post(url + "carta/").status_code, 404)


@patch("vagas.ia.analisar_vaga", return_value=ANALISE)
@patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
class CurriculoEAnaliseTests(APITestCase):
    """A IA é simulada (mock): os testes não gastam a cota do Gemini."""

    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("maria@x.com", "maria@x.com", "senha"))
        self.vaga = self.client.post("/api/vagas/", VAGA).data

    def test_curriculo_estrutura_uma_vez_por_texto(self, estruturar, analisar):
        self.assertEqual(self.client.get("/api/curriculo/").status_code, 404)
        self.assertEqual(self.client.put("/api/curriculo/", {"texto": CURRICULO}).data["dados"], DADOS)
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.assertEqual(estruturar.call_count, 1)
        self.client.put("/api/curriculo/", {"texto": CURRICULO + " Inglês fluente."})
        self.assertEqual(estruturar.call_count, 2)

    def test_curriculo_curto_e_rejeitado(self, estruturar, analisar):
        self.assertEqual(self.client.put("/api/curriculo/", {"texto": "oi"}).status_code, 400)

    def test_curriculo_fica_salvo_mesmo_se_a_ia_falhar(self, estruturar, analisar):
        estruturar.side_effect = ErroIA("Limite", "limite")
        resposta = self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(resposta.data["codigo"], "limite")
        salvo = self.client.get("/api/curriculo/").data
        self.assertEqual(salvo["texto"], CURRICULO)
        self.assertTrue(salvo["desatualizado"])

    def test_analise_usa_cache_ate_a_vaga_mudar(self, estruturar, analisar):
        url = f"/api/vagas/{self.vaga['id']}/analise/"
        self.assertEqual(self.client.post(url).status_code, 400)  # sem currículo
        self.client.put("/api/curriculo/", {"texto": CURRICULO})

        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["nota"], 72)
        self.assertFalse(resposta.data["desatualizada"])
        self.assertEqual(self.client.post(url).status_code, 200)  # cache
        self.assertEqual(analisar.call_count, 1)
        self.assertEqual(self.client.get(f"/api/vagas/{self.vaga['id']}/").data["ultima_nota"], 72)

        self.client.patch(f"/api/vagas/{self.vaga['id']}/", {"descricao": "Python, SQL e AWS"})
        self.assertTrue(self.client.get(url).data["desatualizada"])
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(analisar.call_count, 2)

    def test_mudar_so_o_status_nao_invalida_o_cache(self, estruturar, analisar):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        url = f"/api/vagas/{self.vaga['id']}/analise/"
        self.client.post(url)
        self.client.patch(f"/api/vagas/{self.vaga['id']}/", {"status": "entrevista"})
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(analisar.call_count, 1)

    def test_resposta_invalida_ou_erro_da_ia_viram_502(self, estruturar, analisar):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        url = f"/api/vagas/{self.vaga['id']}/analise/"
        analisar.return_value = {**ANALISE, "nota": 150}
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(resposta.data["codigo"], "formato_invalido")
        analisar.side_effect = ErroIA("Limite de requisições", "limite")
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(resposta.data, {"detail": "Limite de requisições", "codigo": "limite"})
        self.assertEqual(self.client.get(url).status_code, 404)  # nada foi salvo


@patch("vagas.ia.escrever_carta", return_value=CARTA)
@patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
class CartaTests(APITestCase):
    def setUp(self):
        maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        Perfil.objects.create(usuario=maria, nome="Maria Silva")
        self.client.force_authenticate(maria)
        self.vaga = self.client.post("/api/vagas/", VAGA).data
        self.url = f"/api/vagas/{self.vaga['id']}/carta/"

    def test_precisa_de_curriculo(self, estruturar, escrever):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url).status_code, 400)
        escrever.assert_not_called()

    def test_gera_edita_e_gera_outra_versao(self, estruturar, escrever):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})

        resposta = self.client.post(self.url, {"tom": "formal"})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["texto"], CARTA["carta"])
        self.assertEqual(resposta.data["fatos_usados"], CARTA["fatos_usados"])
        self.assertEqual((resposta.data["tom"], resposta.data["tamanho"]), ("formal", "curta"))
        self.assertFalse(resposta.data["editada"])
        # A IA recebe o currículo estruturado, o nome do usuário, o tom e o tamanho.
        dados, vaga, nome, tom, tamanho, analise = escrever.call_args.args
        self.assertEqual((dados, vaga.id, nome, tom, tamanho, analise), (DADOS, self.vaga["id"], "Maria Silva", "formal", "curta", None))

        resposta = self.client.patch(self.url, {"texto": "Minha versão editada da carta."})
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.data["editada"])
        self.assertEqual(self.client.get(self.url).data["texto"], "Minha versão editada da carta.")

        resposta = self.client.post(self.url, {"tom": "entusiasmado", "tamanho": "media"})
        self.assertEqual(resposta.status_code, 201)
        self.assertFalse(resposta.data["editada"])
        self.assertEqual(resposta.data["tom"], "entusiasmado")
        self.assertEqual(escrever.call_count, 2)

    @patch("vagas.ia.analisar_vaga", return_value=ANALISE)
    def test_usa_a_analise_da_vaga_quando_existe(self, analisar, estruturar, escrever):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.client.post(f"/api/vagas/{self.vaga['id']}/analise/")
        self.client.post(self.url)
        self.assertEqual(escrever.call_args.args[5]["lacunas"], ["SQL"])

    def test_carta_fica_desatualizada_quando_o_curriculo_muda(self, estruturar, escrever):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.client.post(self.url)
        self.client.put("/api/curriculo/", {"texto": CURRICULO + " Inglês fluente."})
        self.assertTrue(self.client.get(self.url).data["desatualizada"])

    def test_validacoes(self, estruturar, escrever):
        self.assertEqual(self.client.patch(self.url, {"texto": "oi"}).status_code, 404)  # sem carta
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.assertEqual(self.client.post(self.url, {"tom": "bravo"}).status_code, 400)
        self.assertEqual(self.client.post(self.url, {"tamanho": "enorme"}).status_code, 400)
        self.client.post(self.url)
        self.assertEqual(self.client.patch(self.url, {"texto": "   "}).status_code, 400)
        self.assertEqual(self.client.patch(self.url, {"texto": "x" * 6001}).status_code, 400)

    def test_carta_invalida_ou_erro_da_ia_nao_salvam_nada(self, estruturar, escrever):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        escrever.return_value = {"carta": "Curta demais.", "fatos_usados": ["Python"]}
        self.assertEqual(self.client.post(self.url).status_code, 502)
        escrever.return_value = {**CARTA, "fatos_usados": []}
        self.assertEqual(self.client.post(self.url).status_code, 502)
        escrever.side_effect = ErroIA("Demorou", "tempo_esgotado")
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(resposta.data["codigo"], "tempo_esgotado")
        self.assertEqual(self.client.get(self.url).status_code, 404)


def resposta_gemini(conteudo):
    """Imita o corpo HTTP do Gemini com `conteudo` (dict ou texto) no lugar do JSON gerado."""
    texto = conteudo if isinstance(conteudo, str) else json.dumps(conteudo)
    corpo = {"candidates": [{"content": {"parts": [{"text": texto}]}}]}
    return io.BytesIO(json.dumps(corpo).encode("utf-8"))


def erro_http(codigo):
    return urllib.error.HTTPError(ia.URL, codigo, "erro", {}, io.BytesIO(b"{}"))


@override_settings(GEMINI_API_KEY="chave-de-teste")
@patch("vagas.ia.time.sleep")  # não espera de verdade entre as tentativas
@patch("vagas.ia.urllib.request.urlopen")
class ErrosDaIATests(SimpleTestCase):
    """Como `chamar_gemini` traduz cada falha do Gemini em ErroIA (sem rede de verdade)."""

    def chamar(self):
        return ia.chamar_gemini("prompt", ia.SCHEMA_ANALISE)

    def codigo_do_erro(self):
        with self.assertRaises(ErroIA) as contexto:
            self.chamar()
        return contexto.exception.codigo

    def test_resposta_valida(self, urlopen, dormir):
        urlopen.return_value = resposta_gemini(ANALISE)
        self.assertEqual(self.chamar(), ANALISE)
        enviado = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(enviado["generationConfig"]["responseMimeType"], "application/json")

    @override_settings(GEMINI_API_KEY="")
    def test_sem_chave(self, urlopen, dormir):
        self.assertEqual(self.codigo_do_erro(), "sem_chave")
        urlopen.assert_not_called()

    def test_limite_de_requisicoes_nao_tenta_de_novo(self, urlopen, dormir):
        urlopen.side_effect = erro_http(429)
        self.assertEqual(self.codigo_do_erro(), "limite")
        self.assertEqual(urlopen.call_count, 1)

    def test_tempo_esgotado(self, urlopen, dormir):
        urlopen.side_effect = TimeoutError()
        self.assertEqual(self.codigo_do_erro(), "tempo_esgotado")
        urlopen.side_effect = urllib.error.URLError(TimeoutError())
        self.assertEqual(self.codigo_do_erro(), "tempo_esgotado")

    def test_sem_conexao_e_chave_recusada(self, urlopen, dormir):
        urlopen.side_effect = urllib.error.URLError("Name or service not known")
        self.assertEqual(self.codigo_do_erro(), "sem_conexao")
        urlopen.side_effect = erro_http(403)
        self.assertEqual(self.codigo_do_erro(), "recusado")

    def test_servidor_instavel_tenta_mais_uma_vez(self, urlopen, dormir):
        urlopen.side_effect = [erro_http(503), resposta_gemini(ANALISE)]
        self.assertEqual(self.chamar(), ANALISE)
        self.assertEqual(urlopen.call_count, 2)

        urlopen.reset_mock()
        urlopen.side_effect = [erro_http(503), erro_http(500)]
        self.assertEqual(self.codigo_do_erro(), "indisponivel")
        self.assertEqual(urlopen.call_count, 2)

    def test_json_invalido_tenta_mais_uma_vez(self, urlopen, dormir):
        urlopen.side_effect = [resposta_gemini('{"nota": 7'), resposta_gemini(["lista", "não", "objeto"])]
        self.assertEqual(self.codigo_do_erro(), "formato_invalido")
        self.assertEqual(urlopen.call_count, 2)

    def test_resposta_sem_candidates(self, urlopen, dormir):
        # Acontece quando o Gemini bloqueia o pedido por segurança.
        urlopen.side_effect = lambda *a, **k: io.BytesIO(b'{"promptFeedback": {"blockReason": "SAFETY"}}')
        self.assertEqual(self.codigo_do_erro(), "formato_invalido")
