"""Testes do envio do currículo em PDF (POST /api/curriculo/pdf/).

Os PDFs usados aqui são montados na mão por `pdf_de_texto`, byte a byte: assim
os testes não dependem de arquivo de exemplo no repositório nem de internet.
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from . import pdf
from .models import Curriculo
from .tests import CURRICULO, DADOS

PAGINA = [
    "Maria Silva",
    "Engenharia de Computacao no Insper (2023-2027)",
    "Experiencia: estagio em dados na ACME, com Python e SQL",
    "Habilidades: Python, Django, React, SQL",
]


def pdf_de_texto(paginas):
    """Um PDF válido com uma página por item de `paginas` (cada item é uma lista de linhas)."""
    # Objetos fixos: 1 = catálogo, 2 = árvore de páginas, 3 = fonte.
    # Depois vêm os pares (página, conteúdo): 4 e 5, 6 e 7...
    ids = [4 + 2 * indice for indice in range(len(paginas))]
    kids = " ".join(f"{id_} 0 R" for id_ in ids)
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(paginas)} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    for id_, linhas in zip(ids, paginas):
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {id_ + 1} 0 R >>".encode()
        )
        desenho = "\n".join(f"({linha}) Tj T*" for linha in linhas)
        conteudo = f"BT /F1 12 Tf 14 TL 72 720 Td\n{desenho}\nET".encode("latin-1")
        objetos.append(
            f"<< /Length {len(conteudo)} >>".encode() + b"\nstream\n" + conteudo + b"\nendstream"
        )

    arquivo, posicoes = bytearray(b"%PDF-1.4\n"), []
    for numero, objeto in enumerate(objetos, start=1):
        posicoes.append(len(arquivo))
        arquivo += f"{numero} 0 obj\n".encode() + objeto + b"\nendobj\n"
    inicio_xref = len(arquivo)
    arquivo += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for posicao in posicoes:
        arquivo += f"{posicao:010d} 00000 n \n".encode()
    arquivo += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode()
    return bytes(arquivo)


def upload(conteudo, nome="curriculo.pdf"):
    return SimpleUploadedFile(nome, conteudo, content_type="application/pdf")


class EnvioDePdfTests(APITestCase):
    def setUp(self):
        self.maria = User.objects.create_user("maria@x.com", "maria@x.com", "senha")
        self.client.force_authenticate(self.maria)

    def enviar(self, conteudo, nome="curriculo.pdf"):
        return self.client.post(
            "/api/curriculo/pdf/", {"arquivo": upload(conteudo, nome)}, format="multipart"
        )

    def test_le_o_texto_do_pdf_sem_salvar_nada(self):
        resposta = self.enviar(pdf_de_texto([PAGINA]))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Maria Silva", resposta.data["texto"])
        self.assertIn("Python, Django, React, SQL", resposta.data["texto"])
        self.assertEqual(resposta.data["paginas"], 1)
        self.assertFalse(resposta.data["cortado"])
        # A rota só extrai: o currículo continua não existindo até o PUT.
        self.assertFalse(Curriculo.objects.filter(usuario=self.maria).exists())

    @patch("vagas.ia.estruturar_curriculo", return_value=DADOS)
    def test_texto_lido_do_pdf_pode_ser_salvo_no_curriculo(self, estruturar):
        texto = self.enviar(pdf_de_texto([PAGINA])).data["texto"]
        resposta = self.client.put("/api/curriculo/", {"texto": texto})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["dados"], DADOS)
        self.assertFalse(resposta.data["desatualizado"])

    def test_pdf_sem_camada_de_texto_pede_para_colar(self):
        # Uma página em branco é o que sobra de um currículo escaneado (só imagem).
        resposta = self.enviar(pdf_de_texto([[]]))
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data["codigo"], "sem_texto")
        self.assertIn("cole no campo", resposta.data["detail"])

    def test_arquivo_que_nao_e_pdf_e_recusado_pela_extensao(self):
        resposta = self.enviar(CURRICULO.encode(), nome="curriculo.docx")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data["codigo"], "tipo")

    def test_arquivo_corrompido_com_nome_de_pdf_e_recusado(self):
        resposta = self.enviar(b"nao sou um pdf de verdade" * 10)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data["codigo"], "invalido")

    def test_pdf_grande_e_recusado_antes_de_ser_lido(self):
        with patch.object(pdf, "TAMANHO_MAX", 1024 * 1024):
            resposta = self.enviar(pdf_de_texto([PAGINA]) + b"%" * (1024 * 1024))
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data["codigo"], "grande")

    def test_le_so_as_primeiras_paginas_e_avisa_que_cortou(self):
        with patch.object(pdf, "MAX_PAGINAS", 1):
            resposta = self.enviar(pdf_de_texto([PAGINA, ["Pagina 2: projetos e idiomas"]]))
        self.assertEqual(resposta.data["paginas"], 1)
        self.assertTrue(resposta.data["cortado"])
        self.assertNotIn("Pagina 2", resposta.data["texto"])

    def test_junta_as_paginas_num_texto_so(self):
        resposta = self.enviar(pdf_de_texto([PAGINA, ["Projetos: Encaixe, um buscador de vagas"]]))
        self.assertEqual(resposta.data["paginas"], 2)
        self.assertIn("Maria Silva", resposta.data["texto"])
        self.assertIn("Projetos: Encaixe", resposta.data["texto"])

    def test_sem_arquivo_responde_400(self):
        resposta = self.client.post("/api/curriculo/pdf/", {}, format="multipart")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data["codigo"], "sem_arquivo")

    def test_precisa_estar_logado(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.enviar(pdf_de_texto([PAGINA])).status_code, 401)


class ArrumarTests(SimpleTestCase):
    """A limpeza do texto que sai do pypdf."""

    def test_tira_espacos_sobrando_e_linhas_vazias_demais(self):
        bruto = "  Maria   Silva \n\n\n\n Python \t e  SQL   \n"
        self.assertEqual(pdf.arrumar(bruto), "Maria Silva\n\nPython e SQL")

    def test_tira_caracteres_invisiveis(self):
        self.assertEqual(pdf.arrumar("Enge\xadnharia\xa0de Computa\xe7\xe3o"), "Engenharia de Computação")
