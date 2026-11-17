"""Vagas reais do Brasil pela API pública do Adzuna (https://developer.adzuna.com).

Usa só a biblioteca padrão (urllib), como o ia.py. A API devolve só um trecho
da descrição; o anúncio completo fica no `link` (redirect_url do Adzuna).
Termos de uso: cada vaga mostrada precisa do crédito "Adzuna" com link (o
frontend mostra), e o uso acadêmico é permitido no plano grátis.
"""

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

URL = "https://api.adzuna.com/v1/api/jobs/br/search/1"
TEMPO_LIMITE = 15
POR_PAGINA = 15
# Anúncios mais antigos que isso costumam já estar fechados.
MAX_DIAS = 30


class ErroVagas(Exception):
    """A API de vagas não respondeu. `codigo`: sem_chave, limite, indisponivel ou sem_conexao."""

    def __init__(self, mensagem, codigo="indisponivel"):
        super().__init__(mensagem)
        self.codigo = codigo


def limpar(texto, limite):
    """Tira as tags (o Adzuna marca o termo buscado com <strong>) e corta no limite do modelo Vaga."""
    texto = html.unescape(re.sub(r"<[^>]+>", "", texto or ""))
    return re.sub(r"\s+", " ", texto).strip()[:limite]


def normalizar(item):
    """Um resultado do Adzuna no formato dos campos do modelo Vaga (pronto para salvar no kanban)."""
    link = item.get("redirect_url") or ""
    return {
        "id": str(item.get("id", "")),
        "titulo": limpar(item.get("title"), 200),
        "empresa": limpar((item.get("company") or {}).get("display_name"), 200)
        or "Empresa não informada",
        "local": limpar((item.get("location") or {}).get("display_name"), 120),
        "descricao": limpar(item.get("description"), 5000),
        # Link maior que o campo Vaga.link seria recusado ao salvar; cortar quebraria a URL.
        "link": link if len(link) <= 500 else "",
        "criado_em": item.get("created"),
    }


def buscar(termo, cidade=""):
    """Até POR_PAGINA vagas recentes para `termo`, opcionalmente em `cidade`."""
    if not (settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY):
        raise ErroVagas(
            "A busca de vagas reais não está configurada (faltam ADZUNA_APP_ID e ADZUNA_APP_KEY no backend).",
            "sem_chave",
        )
    parametros = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": termo,
        "results_per_page": POR_PAGINA,
        "max_days_old": MAX_DIAS,
        "sort_by": "date",
        "content-type": "application/json",
    }
    if cidade:
        parametros["where"] = cidade
    try:
        with urllib.request.urlopen(
            f"{URL}?{urllib.parse.urlencode(parametros)}", timeout=TEMPO_LIMITE
        ) as resposta:
            dados = json.load(resposta)
    except urllib.error.HTTPError as erro:
        if erro.code == 429:
            raise ErroVagas("Limite de buscas de vagas atingido. Tente de novo mais tarde.", "limite")
        raise ErroVagas(f"A API de vagas respondeu com erro {erro.code}. Tente de novo.")
    except (urllib.error.URLError, TimeoutError):
        raise ErroVagas("Não foi possível falar com a API de vagas.", "sem_conexao")
    except json.JSONDecodeError:
        raise ErroVagas("A API de vagas devolveu uma resposta inesperada.")
    resultados = dados.get("results") if isinstance(dados, dict) else None
    return [normalizar(item) for item in resultados or [] if isinstance(item, dict)]
