"""Chamadas ao Gemini (API REST do Google AI Studio).

Usa só a biblioteca padrão (urllib), sem SDK. A IA sempre responde JSON
no formato do `responseSchema` enviado; quem chama valida o resultado.
"""

import json
import time
import urllib.error
import urllib.request

from django.conf import settings

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
# v2: a análise recebe as preferências e devolve alertas_preferencias.
VERSAO_PROMPT = "v2"
# carta-v2: a carta usa as áreas e a stack de interesse como motivação.
VERSAO_PROMPT_CARTA = "carta-v2"
VERSAO_PROMPT_SUGESTOES = "sugestoes-v1"
VERSAO_PROMPT_RANKING = "ranking-v1"

# Tempo máximo de cada chamada. O gunicorn do deploy espera até 120 s
# (ver README), então duas tentativas de 50 s ainda cabem.
TEMPO_LIMITE = 50
# Erros passageiros (servidor do Google sobrecarregado, JSON cortado)
# ganham mais uma tentativa depois desta pausa, em segundos.
TENTATIVAS = 2
PAUSA_ENTRE_TENTATIVAS = 2


class ErroIA(Exception):
    """A IA não respondeu ou respondeu algo que não dá para usar.

    `codigo` diz o tipo do problema para o frontend escolher o que mostrar:
    sem_chave, limite, tempo_esgotado, sem_conexao, indisponivel,
    recusado ou formato_invalido.
    """

    def __init__(self, mensagem, codigo="erro"):
        super().__init__(mensagem)
        self.codigo = codigo


def _uma_chamada(corpo):
    requisicao = urllib.request.Request(
        URL.format(modelo=settings.GEMINI_MODEL),
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE) as resposta:
            dados = json.load(resposta)
        texto = dados["candidates"][0]["content"]["parts"][0]["text"]
        resultado = json.loads(texto)
        if not isinstance(resultado, dict):
            raise KeyError
        return resultado
    except urllib.error.HTTPError as erro:
        if erro.code == 429:
            raise ErroIA(
                "Limite de requisições da IA atingido. Espere um minuto e tente de novo.",
                "limite",
            )
        if erro.code >= 500:
            raise ErroIA(
                "O serviço de IA está instável agora. Tente de novo em instantes.",
                "indisponivel",
            )
        raise ErroIA(
            f"A IA recusou o pedido (erro {erro.code}). Confira a GEMINI_API_KEY do backend.",
            "recusado",
        )
    except TimeoutError:
        raise ErroIA("A IA demorou demais para responder. Tente de novo.", "tempo_esgotado")
    except urllib.error.URLError as erro:
        if isinstance(erro.reason, TimeoutError):
            raise ErroIA("A IA demorou demais para responder. Tente de novo.", "tempo_esgotado")
        raise ErroIA("Não foi possível falar com a IA (sem conexão).", "sem_conexao")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ErroIA(
            "A IA devolveu uma resposta em formato inesperado. Tente de novo.",
            "formato_invalido",
        )


def chamar_gemini(prompt, schema, temperatura=0.2):
    """Manda o prompt e devolve o JSON da resposta já convertido em dict.

    Falhas passageiras (erro 5xx do Google ou JSON fora do formato) são
    tentadas de novo uma vez. Limite de requisições e tempo esgotado não:
    tentar de novo na hora só gastaria cota e deixaria o usuário esperando.
    """
    if not settings.GEMINI_API_KEY:
        raise ErroIA("GEMINI_API_KEY não configurada no backend.", "sem_chave")
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": temperatura,
        },
    }
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return _uma_chamada(corpo)
        except ErroIA as erro:
            passageiro = erro.codigo in ("indisponivel", "formato_invalido")
            if not passageiro or tentativa == TENTATIVAS:
                raise
            time.sleep(PAUSA_ENTRE_TENTATIVAS)


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
        "alertas_preferencias": LISTA_DE_TEXTOS,
    },
    "required": [
        "nota",
        "resumo",
        "requisitos_atendidos",
        "lacunas",
        "sugestoes",
        "alertas_preferencias",
    ],
}

SCHEMA_SUGESTOES = {
    "type": "OBJECT",
    "properties": {
        "cargos": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "cargo": {"type": "STRING"},
                    "area": {"type": "STRING"},
                    "nota": {"type": "INTEGER"},
                    "por_que": {"type": "STRING"},
                    "busca": {"type": "STRING"},
                    "palavras_chave": LISTA_DE_TEXTOS,
                },
                "required": ["cargo", "area", "nota", "por_que", "busca", "palavras_chave"],
            },
        },
    },
    "required": ["cargos"],
}

SCHEMA_CARTA = {
    "type": "OBJECT",
    "properties": {
        "carta": {"type": "STRING"},
        "fatos_usados": LISTA_DE_TEXTOS,
    },
    "required": ["carta", "fatos_usados"],
}


def texto_da_vaga(vaga):
    return (
        f"Cargo: {vaga.titulo}\nEmpresa: {vaga.empresa}\n"
        f"Local: {vaga.local or 'não informado'}\nDescrição:\n{vaga.descricao}"
    )


def estruturar_curriculo(texto):
    prompt = (
        "Você recebe o texto de um currículo colado por um estudante. "
        "Organize as informações no JSON pedido, em português. "
        "Use só o que está escrito no texto: não invente cursos, empresas, datas "
        "nem habilidades. Se uma seção não aparece, devolva uma lista vazia.\n\n"
        f"CURRÍCULO:\n{texto}"
    )
    return chamar_gemini(prompt, SCHEMA_CURRICULO)


# Como pedir a nota em cada versão do prompt da análise. A v3 (com escala explícita)
# entrou para a comparação do README (python manage.py comparar_prompts); o app usa VERSAO_PROMPT.
INSTRUCAO_NOTA = {
    "v2": (
        "- nota: aderência de 0 a 100 (100 = atende tudo que a vaga pede);\n"
        "- resumo: 2 a 3 frases dizendo se vale se candidatar e por quê;\n"
        "- requisitos_atendidos: requisitos da vaga que o currículo comprova;\n"
    ),
    "v3": (
        "- nota: aderência de 0 a 100. Antes de dar a nota, separe os requisitos da vaga em "
        'obrigatórios (o que ela exige) e desejáveis ("diferencial", "é um plus"). Use esta escala:\n'
        "  85 a 100: o currículo comprova todos os obrigatórios e a maior parte dos desejáveis;\n"
        "  65 a 84: comprova quase todos os obrigatórios;\n"
        "  40 a 64: comprova parte dos obrigatórios e tem lacunas importantes;\n"
        "  0 a 39: não comprova a maioria dos obrigatórios ou é de outra área.\n"
        "  Em vaga de estágio, disciplinas e projetos acadêmicos contam como experiência;\n"
        "- resumo: 2 a 3 frases dizendo se vale se candidatar e por quê;\n"
        "- requisitos_atendidos: requisitos da vaga que o currículo comprova, cada um com a "
        'evidência do currículo (ex.: "SQL: projeto de BI na disciplina de Banco de Dados");\n'
    ),
}


def analisar_vaga(dados_curriculo, vaga, preferencias=None, versao=VERSAO_PROMPT):
    """`preferencias` (opcional) é o dict de Preferencias.para_ia(): vira alertas, não muda a nota.

    `vaga` só precisa de titulo, empresa, local e descricao (serve um objeto não salvo).
    """
    if preferencias:
        instrucao_alertas = (
            "- alertas_preferencias: pontos da vaga que vão contra as preferências do candidato "
            "(tipo de vaga, modalidade, cidade, stack que ele quer usar ou o que ele prefere "
            "evitar). Em cada alerta, diga qual preferência é afetada e o que a vaga diz "
            '(ex.: "Você prefere vagas remotas, e esta é presencial em Campinas."). '
            "Só aponte o que a vaga diz claramente; se ela não informa, não é alerta. "
            "Lista vazia se não houver conflito.\n"
            "As preferências não mudam a nota: a nota mede só o currículo contra a vaga.\n"
        )
        bloco_preferencias = (
            f"PREFERÊNCIAS DO CANDIDATO:\n{json.dumps(preferencias, ensure_ascii=False)}\n\n"
        )
    else:
        instrucao_alertas = (
            "- alertas_preferencias: lista vazia (o candidato não informou preferências).\n"
        )
        bloco_preferencias = ""
    prompt = (
        "Você é um recrutador que ajuda estudantes a decidir se vale a pena se "
        "candidatar a uma vaga. Compare o currículo (em JSON) com a vaga e responda "
        "em português, no JSON pedido:\n"
        f"{INSTRUCAO_NOTA[versao]}"
        "- lacunas: requisitos da vaga que o currículo não mostra;\n"
        "- sugestoes: ações concretas para melhorar a candidatura;\n"
        f"{instrucao_alertas}"
        "Baseie-se só no que está no currículo e na vaga; não suponha experiências "
        "que não foram escritas.\n\n"
        f"{bloco_preferencias}"
        f"CURRÍCULO:\n{json.dumps(dados_curriculo, ensure_ascii=False)}\n\n"
        f"VAGA:\n{texto_da_vaga(vaga)}"
    )
    return chamar_gemini(prompt, SCHEMA_ANALISE)


TONS = {
    "formal": "formal e respeitoso, sem gírias nem exclamações",
    "neutro": "profissional e direto, cordial sem exageros",
    "entusiasmado": "caloroso e animado, mostrando interesse real pela empresa, sem clichês",
}
TAMANHOS = {
    "curta": "2 ou 3 parágrafos curtos, entre 120 e 180 palavras",
    "media": "3 ou 4 parágrafos, entre 220 e 300 palavras",
}


def escrever_carta(dados_curriculo, vaga, nome, tom, tamanho, analise=None, preferencias=None):
    """Escreve a carta de apresentação usando só fatos do currículo estruturado.

    `analise` (opcional) é o resultado da análise da vaga: as lacunas ajudam a
    IA a tratar com honestidade o que o currículo não mostra.
    `preferencias` (opcional, de Preferencias.para_ia()): as áreas e a stack de
    interesse viram motivação na carta. Cidade, modalidade e o que a pessoa
    prefere evitar ficam de fora, porque não cabem numa carta.
    """
    contexto_analise = ""
    if analise:
        contexto_analise = (
            "ANÁLISE JÁ FEITA DESTA VAGA (use para escolher o que destacar):\n"
            f"Requisitos atendidos: {json.dumps(analise.get('requisitos_atendidos', []), ensure_ascii=False)}\n"
            f"Lacunas: {json.dumps(analise.get('lacunas', []), ensure_ascii=False)}\n\n"
        )
    interesses = {
        chave: valor
        for chave, valor in (preferencias or {}).items()
        if chave in ("areas_de_interesse", "stack_que_quer_usar")
    }
    contexto_interesses = ""
    if interesses:
        contexto_interesses = (
            "INTERESSES QUE O CANDIDATO MARCOU (use só como motivação, quando tiverem a ver "
            "com a vaga; interesse não é experiência, então não diga que ele já trabalhou "
            "com algo que não está no currículo):\n"
            f"{json.dumps(interesses, ensure_ascii=False)}\n\n"
        )
    prompt = (
        "Você escreve cartas de apresentação para estudantes que vão se candidatar "
        "a vagas de estágio ou de início de carreira. Escreva, em português do Brasil "
        "e em primeira pessoa, uma carta para a vaga abaixo.\n\n"
        "REGRAS:\n"
        "- Use SOMENTE fatos que estão no currículo (em JSON). Não invente cursos, "
        "empresas, cargos, projetos, ferramentas, números nem resultados.\n"
        "- Se a vaga pede algo que o currículo não mostra, não finja que a pessoa sabe. "
        "Se for importante, cite no máximo uma dessas lacunas, com honestidade, ligada "
        "ao que a pessoa já sabe e à vontade de aprender.\n"
        "- Ligue os fatos do currículo ao que a vaga pede; não repita o currículo inteiro.\n"
        f"- Tom: {TONS[tom]}.\n"
        f"- Tamanho: {TAMANHOS[tamanho]}.\n"
        f"- Comece com uma saudação à equipe da {vaga.empresa} e termine com uma "
        f"despedida e o nome {nome}.\n"
        "- Texto corrido: sem títulos, marcadores nem campos para preencher como [empresa].\n\n"
        "RESPONDA no JSON pedido:\n"
        "- carta: o texto completo, com os parágrafos separados por uma linha em branco;\n"
        "- fatos_usados: cada fato do currículo que a carta usa, curto "
        '(ex.: "Engenharia de Computação · Insper (2023–2027)").\n\n'
        f"{contexto_analise}"
        f"{contexto_interesses}"
        f"CURRÍCULO:\n{json.dumps(dados_curriculo, ensure_ascii=False)}\n\n"
        f"VAGA:\n{texto_da_vaga(vaga)}"
    )
    # Temperatura maior que a da análise: "Gerar outra versão" precisa mudar o texto.
    return chamar_gemini(prompt, SCHEMA_CARTA, temperatura=0.7)


def sugerir_buscas(dados_curriculo, preferencias=None):
    """Sugere cargos para procurar, com o texto de busca e palavras-chave de cada um."""
    if preferencias:
        bloco_preferencias = (
            f"PREFERÊNCIAS DO CANDIDATO:\n{json.dumps(preferencias, ensure_ascii=False)}\n\n"
        )
        regra_preferencias = (
            "- Priorize as áreas de interesse e a stack que a pessoa quer usar. No máximo uma "
            "sugestão pode sair das áreas marcadas, e só se o currículo mostrar uma ponte clara.\n"
            "- Use o tipo de vaga preferido no nome do cargo. Se houver mais de um, use o que "
            "combina melhor com o currículo.\n"
            "- Não sugira nada que bata com o que a pessoa prefere evitar.\n"
        )
    else:
        bloco_preferencias = ""
        regra_preferencias = (
            "- A pessoa não informou preferências: escolha áreas e o nível (estágio, trainee "
            "ou júnior) que combinam com o currículo.\n"
        )
    prompt = (
        "Você é um orientador de carreira de estudantes e recém-formados. A partir do "
        "currículo (em JSON), sugira de 3 a 4 cargos para a pessoa procurar em sites de "
        "vagas como LinkedIn, Gupy e Indeed. Responda em português do Brasil, no JSON pedido:\n"
        "- cargo: nome do cargo como aparece nos anúncios, já com o nível "
        '(ex.: "Estágio em Dados", "Desenvolvedor Júnior Back-end");\n'
        '- area: a área de atuação (ex.: "Dados", "Desenvolvimento web");\n'
        "- nota: aderência estimada, de 0 a 100, entre o currículo e as vagas típicas desse cargo;\n"
        "- por_que: 1 ou 2 frases citando fatos do currículo (e as preferências, se houver) "
        "que justificam a sugestão;\n"
        "- busca: o texto para digitar na busca dos sites de vagas, com 2 a 4 palavras, sem "
        'cidade nem modalidade (ex.: "estágio dados");\n'
        "- palavras_chave: 3 a 5 termos curtos que aparecem nos anúncios desse cargo, para "
        "refinar a busca.\n\n"
        "REGRAS:\n"
        f"{regra_preferencias}"
        "- Não invente experiências: o por_que só pode citar o que está no currículo e nas "
        "preferências.\n"
        "- Ordene da maior para a menor nota.\n\n"
        f"{bloco_preferencias}"
        f"CURRÍCULO:\n{json.dumps(dados_curriculo, ensure_ascii=False)}"
    )
    # Um pouco de variação: "Atualizar sugestões" deve trazer ideias novas.
    return chamar_gemini(prompt, SCHEMA_SUGESTOES, temperatura=0.6)


SCHEMA_RANKING = {
    "type": "OBJECT",
    "properties": {
        "vagas": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "nota": {"type": "INTEGER"},
                    "motivo": {"type": "STRING"},
                },
                "required": ["id", "nota", "motivo"],
            },
        },
    },
    "required": ["vagas"],
}


def ranquear_vagas(dados_curriculo, vagas, preferencias=None):
    """Nota de aderência rápida para cada vaga da lista ([{id, titulo, empresa, local, descricao}]).

    Uma chamada só para a lista inteira; a análise completa continua sendo a do kanban.
    """
    resumo_vagas = [
        {chave: vaga[chave] for chave in ("id", "titulo", "empresa", "local", "descricao")}
        for vaga in vagas
    ]
    bloco_preferencias = ""
    if preferencias:
        bloco_preferencias = (
            f"PREFERÊNCIAS DO CANDIDATO:\n{json.dumps(preferencias, ensure_ascii=False)}\n\n"
        )
    prompt = (
        "Você é um recrutador que ajuda um estudante a escolher a quais vagas se candidatar. "
        "Para CADA vaga da lista, dê uma nota de aderência do currículo (em JSON) à vaga e "
        "explique em uma frase curta. Responda em português, no JSON pedido:\n"
        "- id: o id da vaga, igual ao da lista;\n"
        "- nota: 0 a 100 (100 = o currículo comprova tudo o que a vaga pede). A descrição é "
        "só um trecho do anúncio: julgue pelo que está escrito, sem supor requisitos;\n"
        '- motivo: uma frase com o principal ponto a favor ou contra (ex.: "Pede Python e '
        'SQL, que você usou no projeto de BI; falta Power BI.").\n'
        "Baseie-se só no currículo e na vaga: não suponha experiências que não foram escritas. "
        "Se a vaga for contra as preferências (nível, modalidade, cidade, o que evitar), diga "
        "isso no motivo, mas a nota mede só o currículo.\n\n"
        f"{bloco_preferencias}"
        f"CURRÍCULO:\n{json.dumps(dados_curriculo, ensure_ascii=False)}\n\n"
        f"VAGAS:\n{json.dumps(resumo_vagas, ensure_ascii=False)}"
    )
    return chamar_gemini(prompt, SCHEMA_RANKING)
