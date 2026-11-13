"""Chamadas ao Gemini (API REST do Google AI Studio).

Usa só a biblioteca padrão (urllib), sem SDK. A IA sempre responde JSON
no formato do `responseSchema` enviado; quem chama valida o resultado.
"""

import json
import urllib.error
import urllib.request

from django.conf import settings

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
VERSAO_PROMPT = "v1"


class ErroIA(Exception):
    """A IA não respondeu ou respondeu algo que não dá para usar."""


def chamar_gemini(prompt, schema):
    """Manda o prompt e devolve o JSON da resposta já convertido em dict."""
    if not settings.GEMINI_API_KEY:
        raise ErroIA("GEMINI_API_KEY não configurada no backend.")
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.2,
        },
    }
    requisicao = urllib.request.Request(
        URL.format(modelo=settings.GEMINI_MODEL),
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=60) as resposta:
            dados = json.load(resposta)
        texto = dados["candidates"][0]["content"]["parts"][0]["text"]
        resultado = json.loads(texto)
        if not isinstance(resultado, dict):
            raise KeyError
        return resultado
    except urllib.error.HTTPError as erro:
        if erro.code == 429:
            raise ErroIA("Limite de requisições da IA atingido. Tente de novo em instantes.")
        raise ErroIA(f"A IA respondeu com erro {erro.code}.")
    except (urllib.error.URLError, TimeoutError):
        raise ErroIA("Não foi possível falar com a IA (sem conexão ou tempo esgotado).")
    except (KeyError, IndexError, json.JSONDecodeError):
        raise ErroIA("A IA devolveu uma resposta em formato inesperado.")


LISTA_DE_TEXTOS = {"type": "ARRAY", "items": {"type": "STRING"}}

SCHEMA_CURRICULO = {
    "type": "OBJECT",
    "properties": {
        "resumo": {"type": "STRING"},
        "formacao": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "curso": {"type": "STRING"},
                    "instituicao": {"type": "STRING"},
                    "periodo": {"type": "STRING"},
                },
                "required": ["curso", "instituicao"],
            },
        },
        "experiencias": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "cargo": {"type": "STRING"},
                    "empresa": {"type": "STRING"},
                    "periodo": {"type": "STRING"},
                    "atividades": LISTA_DE_TEXTOS,
                },
                "required": ["cargo", "empresa"],
            },
        },
        "habilidades": LISTA_DE_TEXTOS,
        "idiomas": LISTA_DE_TEXTOS,
        "projetos": LISTA_DE_TEXTOS,
    },
    "required": ["resumo", "formacao", "experiencias", "habilidades", "idiomas", "projetos"],
}

SCHEMA_ANALISE = {
    "type": "OBJECT",
    "properties": {
        "nota": {"type": "INTEGER"},
        "resumo": {"type": "STRING"},
        "requisitos_atendidos": LISTA_DE_TEXTOS,
        "lacunas": LISTA_DE_TEXTOS,
        "sugestoes": LISTA_DE_TEXTOS,
    },
    "required": ["nota", "resumo", "requisitos_atendidos", "lacunas", "sugestoes"],
}


def estruturar_curriculo(texto):
    prompt = (
        "Você recebe o texto de um currículo colado por um estudante. "
        "Organize as informações no JSON pedido, em português. "
        "Use só o que está escrito no texto: não invente cursos, empresas, datas "
        "nem habilidades. Se uma seção não aparece, devolva uma lista vazia.\n\n"
        f"CURRÍCULO:\n{texto}"
    )
    return chamar_gemini(prompt, SCHEMA_CURRICULO)


def analisar_vaga(dados_curriculo, vaga):
    prompt = (
        "Você é um recrutador que ajuda estudantes a decidir se vale a pena se "
        "candidatar a uma vaga. Compare o currículo (em JSON) com a vaga e responda "
        "em português, no JSON pedido:\n"
        "- nota: aderência de 0 a 100 (100 = atende tudo que a vaga pede);\n"
        "- resumo: 2 a 3 frases dizendo se vale se candidatar e por quê;\n"
        "- requisitos_atendidos: requisitos da vaga que o currículo comprova;\n"
        "- lacunas: requisitos da vaga que o currículo não mostra;\n"
        "- sugestoes: ações concretas para melhorar a candidatura.\n"
        "Baseie-se só no que está no currículo e na vaga; não suponha experiências "
        "que não foram escritas.\n\n"
        f"CURRÍCULO:\n{json.dumps(dados_curriculo, ensure_ascii=False)}\n\n"
        f"VAGA:\nCargo: {vaga.titulo}\nEmpresa: {vaga.empresa}\n"
        f"Local: {vaga.local or 'não informado'}\nDescrição:\n{vaga.descricao}"
    )
    return chamar_gemini(prompt, SCHEMA_ANALISE)
