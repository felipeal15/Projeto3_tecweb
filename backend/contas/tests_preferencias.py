from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Preferencias, hash_preferencias

URL = "/api/preferencias/"
COMPLETAS = {
    "areas": ["Dados", "Desenvolvimento web"],
    "tipos": ["estagio"],
    "modalidades": ["hibrido", "remoto"],
    "cidade": "São Paulo, SP",
    "stack": ["Python", "SQL", "React"],
    "evitar": "Vagas com mais de 30 horas semanais",
}


class PreferenciasTests(APITestCase):
    def setUp(self):
        self.maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        self.client.force_authenticate(self.maria)

    def test_exige_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_sem_preferencias_devolve_tudo_vazio(self):
        resposta = self.client.get(URL)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["areas"], [])
        self.assertEqual(resposta.data["cidade"], "")
        # null = nunca salvou: a tela mostra o passo 3 do onboarding.
        self.assertIsNone(resposta.data["atualizado_em"])
        self.assertFalse(Preferencias.objects.exists())

    def test_salva_e_le_de_volta(self):
        resposta = self.client.put(URL, COMPLETAS, format="json")
        self.assertEqual(resposta.status_code, 200)
        self.assertIsNotNone(resposta.data["atualizado_em"])
        lido = self.client.get(URL).data
        for campo, valor in COMPLETAS.items():
            self.assertEqual(lido[campo], valor)

        # Salvar de novo atualiza a mesma linha.
        self.client.put(URL, {**COMPLETAS, "cidade": "Campinas"}, format="json")
        self.assertEqual(Preferencias.objects.count(), 1)
        self.assertEqual(self.client.get(URL).data["cidade"], "Campinas")

    def test_limpa_espacos_vazios_e_repetidos(self):
        corpo = {
            "areas": ["  Dados ", "dados", "", "Produto"],
            "stack": ["Python", "python", "SQL"],
            "tipos": ["estagio", "estagio"],
        }
        resposta = self.client.put(URL, corpo, format="json")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["areas"], ["Dados", "Produto"])
        self.assertEqual(resposta.data["stack"], ["Python", "SQL"])
        self.assertEqual(resposta.data["tipos"], ["estagio"])

    def test_validacoes(self):
        self.assertIn("tipos", self.client.put(URL, {"tipos": ["chefe"]}, format="json").data)
        self.assertIn(
            "modalidades", self.client.put(URL, {"modalidades": ["lua"]}, format="json").data
        )
        resposta = self.client.put(URL, {"areas": [f"Área {i}" for i in range(11)]}, format="json")
        self.assertEqual(resposta.status_code, 400)
        # Erro de item longo vem como mensagem simples (o frontend mostra direto).
        resposta = self.client.put(URL, {"stack": ["x" * 41]}, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data["stack"], ["Cada item pode ter no máximo 40 caracteres."])
        self.assertEqual(self.client.put(URL, {"evitar": "x" * 301}, format="json").status_code, 400)
        self.assertFalse(Preferencias.objects.exists())

    def test_cada_usuario_ve_so_as_suas(self):
        self.client.put(URL, COMPLETAS, format="json")
        joao = User.objects.create_user("joao@x.com", "joao@x.com", "senha")
        self.client.force_authenticate(joao)
        self.assertEqual(self.client.get(URL).data["areas"], [])


class HashEPromptTests(APITestCase):
    def test_hash_vazio_sem_preferencias_e_estavel_na_ordem(self):
        maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        self.assertEqual(hash_preferencias(maria), "")
        vazia = Preferencias.objects.create(usuario=maria)
        self.assertEqual(vazia.hash, "")

        vazia.areas = ["Dados", "Produto"]
        hash_1 = vazia.hash
        vazia.areas = ["Produto", "Dados"]
        self.assertEqual(vazia.hash, hash_1)  # mudar a ordem não invalida o cache
        vazia.cidade = "Recife"
        self.assertNotEqual(vazia.hash, hash_1)

    def test_para_ia_usa_rotulos_e_ignora_campos_vazios(self):
        preferencias = Preferencias(tipos=["estagio", "junior"], modalidades=["remoto"], areas=["Dados"])
        self.assertEqual(
            preferencias.para_ia(),
            {"areas_de_interesse": ["Dados"], "tipos_de_vaga": ["Estágio", "Júnior"], "modalidades": ["Remoto"]},
        )
        self.assertIsNone(Preferencias().para_ia())
