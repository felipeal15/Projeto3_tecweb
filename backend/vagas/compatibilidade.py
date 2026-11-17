"""Filtro do kanban: a vaga vai contra as preferências do usuário?

Lê o texto da vaga procurando o tipo (estágio, trainee, júnior), a modalidade
(presencial, híbrido, remoto) e a cidade. É uma busca por palavras, sem IA:
roda em todas as vagas, na hora e sem gastar cota. Por isso só aponta conflito
quando a vaga diz claramente outra coisa; se ela não informa, não é conflito.
"""

import re
import unicodedata

from contas.models import Preferencias

# Procurados no cargo (o título costuma dizer o nível da vaga).
PADROES_TIPO = {
    "estagio": r"\bestagi|\bintern(ship)?\b",
    "trainee": r"\btrainee\b",
    "junior": r"\bjunior\b|\bjr\b|\bentry[ -]level\b",
}

# Procurados no local da vaga; se ele não diz, na descrição.
PADROES_MODALIDADE = {
    "presencial": r"\bpresencia(l|is)\b|\bon[ -]?site\b",
    "hibrido": r"\bhibrid[oa]s?\b|\bhybrid\b",
    "remoto": r"\bremot[oa]s?\b|\bremote\b|\bhome[ -]?office\b",
}

ROTULOS_TIPO = dict(Preferencias.Tipo.choices)
ROTULOS_MODALIDADE = dict(Preferencias.Modalidade.choices)


def normalizar(texto):
    """Minúsculas e sem acento: "Estágio em São Paulo" -> "estagio em sao paulo"."""
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(letra for letra in sem_acento if not unicodedata.combining(letra))
    return sem_acento.casefold()


def encontrados(padroes, texto):
    """Quais chaves de `padroes` aparecem no texto (já normalizado)."""
    return {chave for chave, padrao in padroes.items() if re.search(padrao, texto)}


def nome_da_cidade(cidade):
    """ "São Paulo, SP" -> "São Paulo" (o estado fica de fora da comparação)."""
    return re.split(r"[,/(]| - ", cidade)[0].strip()


def fora_das_preferencias(vaga, preferencias):
    """Lista do que, na vaga, vai contra as preferências (ex.: ["Júnior", "Presencial"]).

    Lista vazia = a vaga combina, ou não dá para saber pelo texto.
    """
    if preferencias is None:
        return []
    conflitos = []

    tipos_da_vaga = encontrados(PADROES_TIPO, normalizar(vaga.titulo))
    if preferencias.tipos and tipos_da_vaga and not tipos_da_vaga & set(preferencias.tipos):
        conflitos.append(" ou ".join(ROTULOS_TIPO[t] for t in PADROES_TIPO if t in tipos_da_vaga))

    local = normalizar(vaga.local)
    modalidades_da_vaga = encontrados(PADROES_MODALIDADE, local) or encontrados(
        PADROES_MODALIDADE, normalizar(vaga.descricao)
    )
    if (
        preferencias.modalidades
        and modalidades_da_vaga
        and not modalidades_da_vaga & set(preferencias.modalidades)
    ):
        conflitos.append(
            " ou ".join(ROTULOS_MODALIDADE[m] for m in PADROES_MODALIDADE if m in modalidades_da_vaga)
        )

    # Cidade: só vale para vaga que não é 100% remota, e só se o usuário aceita ir ao escritório.
    cidade = nome_da_cidade(preferencias.cidade)
    vaga_so_remota = modalidades_da_vaga == {"remoto"}
    usuario_so_remoto = set(preferencias.modalidades) == {"remoto"}
    if cidade and not vaga_so_remota and not usuario_so_remoto:
        # O que sobra do local sem as palavras de modalidade é a cidade da vaga ("Rio de Janeiro").
        cidade_da_vaga = local
        for padrao in PADROES_MODALIDADE.values():
            cidade_da_vaga = re.sub(padrao, " ", cidade_da_vaga)
        cidade_da_vaga = re.sub(r"[^a-z0-9]+", " ", cidade_da_vaga).strip()
        if cidade_da_vaga and normalizar(cidade) not in local:
            conflitos.append(f"Fora de {cidade}")

    return conflitos
