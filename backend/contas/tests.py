from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Perfil

SENHA = "girassol-azul-42"


class AutenticacaoTests(APITestCase):
    def cadastrar(self, **dados):
        corpo = {"nome": "Maria Silva", "email": "Maria.Silva@Email.com", "senha": SENHA, **dados}
        return self.client.post("/api/auth/cadastro/", corpo)

    def usar_token(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_cadastro_cria_usuario_perfil_e_token(self):
        resposta = self.cadastrar()
        self.assertEqual(resposta.status_code, 201)
        self.assertTrue(resposta.data["token"])
        # O e-mail vira o username, em minúsculas.
        self.assertEqual(resposta.data["usuario"]["email"], "maria.silva@email.com")
        self.assertEqual(resposta.data["usuario"]["nome"], "Maria Silva")
        usuario = User.objects.get(username="maria.silva@email.com")
        self.assertEqual(Perfil.objects.get(usuario=usuario).nome, "Maria Silva")

    def test_cadastro_rejeita_email_repetido(self):
        self.cadastrar()
        resposta = self.cadastrar(email="maria.silva@email.com")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("email", resposta.data)

    def test_cadastro_rejeita_senha_fraca_e_campos_vazios(self):
        resposta = self.cadastrar(senha="12345678")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("senha", resposta.data)

        resposta = self.client.post("/api/auth/cadastro/", {})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(set(resposta.data), {"nome", "email", "senha"})
        self.assertFalse(User.objects.exists())

    def test_login_aceita_email_com_maiusculas(self):
        self.cadastrar()
        resposta = self.client.post(
            "/api/auth/login/", {"email": "MARIA.SILVA@email.com", "senha": SENHA}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.data["token"])
        self.assertEqual(resposta.data["usuario"]["nome"], "Maria Silva")

    def test_login_com_senha_errada(self):
        self.cadastrar()
        resposta = self.client.post(
            "/api/auth/login/", {"email": "maria.silva@email.com", "senha": "outra-senha-99"}
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("non_field_errors", resposta.data)
        self.assertNotIn("token", resposta.data)

    def test_rotas_protegidas_exigem_token(self):
        self.assertEqual(self.client.get("/api/auth/eu/").status_code, 401)
        self.assertEqual(self.client.get("/api/vagas/").status_code, 401)
        self.assertEqual(self.client.get("/api/curriculo/").status_code, 401)
        self.usar_token("token-que-nao-existe")
        self.assertEqual(self.client.get("/api/auth/eu/").status_code, 401)

    def test_eu_devolve_o_dono_do_token(self):
        token = self.cadastrar().data["token"]
        self.usar_token(token)
        resposta = self.client.get("/api/auth/eu/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["email"], "maria.silva@email.com")

    def test_logout_invalida_o_token(self):
        token = self.cadastrar().data["token"]
        self.usar_token(token)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/eu/").status_code, 401)

    def test_superusuario_sem_perfil_tem_nome(self):
        # Contas criadas pelo createsuperuser não têm Perfil; o /eu não pode quebrar.
        admin = User.objects.create_superuser("admin", "admin@x.com", SENHA)
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get("/api/auth/eu/").data["nome"], "admin")
