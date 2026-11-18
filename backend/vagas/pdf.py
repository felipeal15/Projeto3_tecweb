"""Leitura do texto de um PDF de currículo enviado pelo usuário.

Usa o pypdf (Python puro, sem dependência de sistema) e lê só a camada de texto
do arquivo: não tem OCR. Currículo escaneado (foto ou imagem da página) não tem
texto para extrair e cai no erro `sem_texto`, que pede para colar o texto na mão.

O texto extraído não é salvo aqui: a view devolve para a tela, o usuário confere
e o PUT /api/curriculo/ salva como qualquer currículo colado.
"""

import re

from pypdf import PdfReader
from pypdf.errors import DependencyError, FileNotDecryptedError

TAMANHO_MAX = 5 * 1024 * 1024  # 5 MB: sobra para um currículo com foto e ícones.
# Páginas lidas. Currículo tem 1 ou 2; o limite evita processar um PDF enorme por engano.
MAX_PAGINAS = 10
# O texto vai inteiro para o prompt da IA, então tem um teto.
MAX_CARACTERES = 20000
# Mesmo mínimo do CurriculoSerializer: menos que isso não é um currículo.
# PDF de imagem costuma extrair nada ou um punhado de caracteres soltos.
MIN_CARACTERES = 50


class ErroPdf(Exception):
    """Não deu para ler o texto do PDF.

    `codigo` diz o tipo do problema para a tela escolher a mensagem:
    tipo, grande, protegido, invalido ou sem_texto.
    """

    def __init__(self, mensagem, codigo="invalido"):
        super().__init__(mensagem)
        self.codigo = codigo


def arrumar(texto):
    """Deixa o texto do pypdf legível: sem espaços sobrando nem linhas vazias demais."""
    # \x00 aparece em PDF mal formado e o Postgres recusa; \xad é o hífen invisível.
    texto = texto.replace("\x00", "").replace("\xad", "")
    linhas = [re.sub(r"[ \t\xa0]+", " ", linha).strip() for linha in texto.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def extrair_texto(arquivo):
    """O texto de um PDF enviado (UploadedFile do Django).

    Devolve {texto, paginas, cortado}; `cortado` avisa que o PDF tinha mais
    páginas (ou mais texto) do que os limites deste módulo. Levanta ErroPdf
    quando o arquivo não serve.
    """
    if not (arquivo.name or "").lower().endswith(".pdf"):
        raise ErroPdf("Por enquanto só dá para enviar o currículo em PDF.", "tipo")
    if arquivo.size > TAMANHO_MAX:
        raise ErroPdf(
            f"O arquivo passou de {TAMANHO_MAX // (1024 * 1024)} MB. "
            "Exporte o currículo em PDF de novo ou cole o texto no campo.",
            "grande",
        )

    try:
        leitor = PdfReader(arquivo)
        total_paginas = len(leitor.pages)
        partes = [
            pagina.extract_text() or "" for pagina in leitor.pages[:MAX_PAGINAS]
        ]
    except (FileNotDecryptedError, DependencyError) as erro:
        # Protegido por senha (o pypdf tenta a senha vazia) ou com uma criptografia
        # que ele não abre sozinho.
        raise ErroPdf(
            "Este PDF está protegido por senha. Salve uma versão sem senha ou cole o texto no campo.",
            "protegido",
        ) from erro
    except Exception as erro:
        # O próprio pypdf avisa que um PDF corrompido pode levantar qualquer exceção.
        raise ErroPdf(
            "Não foi possível ler este arquivo. Confira se é um PDF de verdade e não está corrompido.",
            "invalido",
        ) from erro

    texto = arrumar("\n\n".join(partes))
    if len(texto) < MIN_CARACTERES:
        raise ErroPdf(
            "Não encontramos texto neste PDF. Se ele for escaneado (uma imagem da página), "
            "copie o texto do currículo e cole no campo abaixo.",
            "sem_texto",
        )
    return {
        "texto": texto[:MAX_CARACTERES],
        "paginas": min(total_paginas, MAX_PAGINAS),
        "cortado": total_paginas > MAX_PAGINAS or len(texto) > MAX_CARACTERES,
    }
