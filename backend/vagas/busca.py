"""Links de busca prontos no LinkedIn, no Gupy e no Indeed.

O Encaixe só monta o endereço: quem abre é o navegador do usuário, e nada
desses sites é lido pelo backend. Os links usam as preferências do momento,
então mudar a cidade ou a modalidade já muda os links, sem chamar a IA.
"""

from urllib.parse import quote, urlencode

from .compatibilidade import nome_da_cidade

# Filtros da busca de vagas do LinkedIn (parâmetros da própria URL do site).
# f_WT = modelo de trabalho; f_E = nível de experiência (1 estágio, 2 júnior/início de carreira).
LINKEDIN_MODALIDADE = {"presencial": "1", "remoto": "2", "hibrido": "3"}
LINKEDIN_NIVEL = {"estagio": "1", "trainee": "2", "junior": "2"}


def links_de_busca(termo, preferencias=None):
    """[{site, url}] para buscar `termo` (ex.: "estágio dados") em cada site."""
    modalidades = list(preferencias.modalidades) if preferencias else []
    tipos = list(preferencias.tipos) if preferencias else []
    cidade = nome_da_cidade(preferencias.cidade) if preferencias else ""
    so_remoto = set(modalidades) == {"remoto"}
    # Quem só quer vaga remota não precisa filtrar por cidade.
    local = "" if so_remoto else cidade

    linkedin = {"keywords": termo, "location": local or "Brasil"}
    codigos = sorted({LINKEDIN_MODALIDADE[m] for m in modalidades if m in LINKEDIN_MODALIDADE})
    if codigos:
        linkedin["f_WT"] = ",".join(codigos)
    niveis = sorted({LINKEDIN_NIVEL[t] for t in tipos if t in LINKEDIN_NIVEL})
    if niveis:
        linkedin["f_E"] = ",".join(niveis)

    indeed = {"q": f"{termo} remoto" if so_remoto else termo}
    if local:
        indeed["l"] = local

    return [
        {"site": "LinkedIn", "url": "https://www.linkedin.com/jobs/search/?" + urlencode(linkedin)},
        # O Gupy só aceita o termo na URL; cidade e modalidade se filtram lá dentro.
        {"site": "Gupy", "url": "https://portal.gupy.io/job-search/term=" + quote(termo)},
        {"site": "Indeed", "url": "https://br.indeed.com/jobs?" + urlencode(indeed)},
    ]
