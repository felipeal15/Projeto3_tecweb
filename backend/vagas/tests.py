from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .ia import ErroIA

CURRICULO = "Maria Silva. Engenharia de Computação no Insper (2023-2027). Python, Django, React."
DADOS = {"resumo": "Estudante", "formacao": [], "experiencias": [], "habilidades": ["Python"], "idiomas": [], "projetos": []}
ANALISE = {"nota": 72, "resumo": "Vale tentar.", "requisitos_atendidos": ["Python"], "lacunas": ["SQL"], "sugestoes": ["Estudar SQL"]}


@patch("vagas.ia.analisar_vaga", return_value=ANALISE)
@patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
class CurriculoEAnaliseTests(APITestCase):
    """A IA é simulada (mock): os testes não gastam a cota do Gemini."""

    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("maria@x.com", "maria@x.com", "senha"))
        self.vaga = self.client.post(
            "/api/vagas/", {"titulo": "Estágio Dev", "empresa": "ACME", "descricao": "Python e SQL"}
        ).data

    def test_curriculo_estrutura_uma_vez_por_texto(self, estruturar, analisar):
        self.assertEqual(self.client.put("/api/curriculo/", {"texto": CURRICULO}).data["dados"], DADOS)
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        self.assertEqual(estruturar.call_count, 1)
        self.client.put("/api/curriculo/", {"texto": CURRICULO + " Inglês fluente."})
        self.assertEqual(estruturar.call_count, 2)

    def test_curriculo_curto_e_rejeitado(self, estruturar, analisar):
        self.assertEqual(self.client.put("/api/curriculo/", {"texto": "oi"}).status_code, 400)

    def test_analise_usa_cache_ate_a_vaga_mudar(self, estruturar, analisar):
        url = f"/api/vagas/{self.vaga['id']}/analise/"
        self.assertEqual(self.client.post(url).status_code, 400)  # sem currículo
        self.client.put("/api/curriculo/", {"texto": CURRICULO})

        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["nota"], 72)
        self.assertEqual(self.client.post(url).status_code, 200)  # cache
        self.assertEqual(analisar.call_count, 1)
        self.assertEqual(self.client.get(f"/api/vagas/{self.vaga['id']}/").data["ultima_nota"], 72)

        self.client.patch(f"/api/vagas/{self.vaga['id']}/", {"descricao": "Python, SQL e AWS"})
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(analisar.call_count, 2)

    def test_resposta_invalida_ou_erro_da_ia_viram_502(self, estruturar, analisar):
        self.client.put("/api/curriculo/", {"texto": CURRICULO})
        url = f"/api/vagas/{self.vaga['id']}/analise/"
        analisar.return_value = {**ANALISE, "nota": 150}
        self.assertEqual(self.client.post(url).status_code, 502)
        analisar.side_effect = ErroIA("Limite de requisições")
        self.assertEqual(self.client.post(url).status_code, 502)
        self.assertEqual(self.client.get(url).status_code, 404)  # nada foi salvo
