"""Compara duas versões do prompt da análise nos pares de docs/avaliacao/pares.json.

    python manage.py comparar_prompts                # v2 x v3, 2 rodadas por par
    python manage.py comparar_prompts --rodadas 1 --pausa 6

Usa a GEMINI_API_KEY de verdade: 11 pares x 2 versões x 2 rodadas = 44 chamadas.
Escreve o resultado em docs/avaliacao/resultado.md.
"""

import json
import time
from pathlib import Path
from statistics import mean
from types import SimpleNamespace

from django.conf import settings
from django.core.management.base import BaseCommand

from vagas import ia
from vagas.serializers import ResultadoAnaliseSerializer

PASTA = Path(settings.BASE_DIR).parent / "docs" / "avaliacao"


def faixa(nota):
    """Mesmas faixas do frontend (src/vagas.js): Alta >= 75, Média >= 50."""
    return "alta" if nota >= 75 else "média" if nota >= 50 else "baixa"


def metricas(linhas, versao):
    """Erro médio, acerto de faixa e variação entre rodadas de uma versão do prompt."""
    erros, acertos, variacoes, falhas = [], 0, [], 0
    for linha in linhas:
        notas = [n for n in linha[versao] if n is not None]
        falhas += len(linha[versao]) - len(notas)
        if not notas:
            continue
        media = mean(notas)
        erros.append(abs(media - linha["referencia"]))
        acertos += faixa(media) == faixa(linha["referencia"])
        if len(notas) > 1:
            variacoes.append(max(notas) - min(notas))
    return {
        "erro_medio": round(mean(erros), 1) if erros else None,
        "acerto_faixa": f"{acertos}/{len(linhas)}",
        "variacao_media": round(mean(variacoes), 1) if variacoes else 0,
        "falhas": falhas,
    }


def tabela(linhas, versoes):
    cabecalho = "| Par | Vaga | Referência | " + " | ".join(versoes) + " |"
    separador = "|" + " --- |" * (3 + len(versoes))
    corpo = [
        f"| {l['id']} | {l['vaga']} | {l['referencia']} | "
        + " | ".join(" / ".join("erro" if n is None else str(n) for n in l[v]) for v in versoes)
        + " |"
        for l in linhas
    ]
    return "\n".join([cabecalho, separador, *corpo])


class Command(BaseCommand):
    help = "Compara versões do prompt da análise no conjunto de pares currículo x vaga."

    def add_arguments(self, parser):
        parser.add_argument("--versoes", nargs=2, default=["v2", "v3"], choices=list(ia.INSTRUCAO_NOTA))
        parser.add_argument("--rodadas", type=int, default=2)
        # O plano grátis do Gemini limita as requisições por minuto.
        parser.add_argument("--pausa", type=float, default=4.0, help="segundos entre chamadas")
        parser.add_argument("--pares", default=str(PASTA / "pares.json"))
        parser.add_argument("--saida", default=str(PASTA / "resultado.md"))

    def handle(self, *args, versoes, rodadas, pausa, pares, saida, **opcoes):
        conjunto = json.loads(Path(pares).read_text(encoding="utf-8"))
        linhas = []
        for par in conjunto["pares"]:
            vaga = SimpleNamespace(**par["vaga"])
            linha = {"id": par["id"], "vaga": f"{par['curriculo']} × {vaga.titulo}", "referencia": par["nota_referencia"]}
            for versao in versoes:
                linha[versao] = []
                for _ in range(rodadas):
                    try:
                        resultado = ResultadoAnaliseSerializer(
                            data=ia.analisar_vaga(conjunto["curriculos"][par["curriculo"]], vaga, versao=versao)
                        )
                        nota = resultado.validated_data["nota"] if resultado.is_valid() else None
                    except ia.ErroIA as erro:
                        self.stderr.write(f"par {par['id']} {versao}: {erro}")
                        nota = None
                    linha[versao].append(nota)
                    time.sleep(pausa)
            self.stdout.write(f"par {linha['id']}: " + ", ".join(f"{v}={linha[v]}" for v in versoes))
            linhas.append(linha)

        resumo = {versao: metricas(linhas, versao) for versao in versoes}
        texto = (
            f"# Comparação de prompts da análise: {versoes[0]} × {versoes[1]}\n\n"
            f"Modelo `{settings.GEMINI_MODEL}`, {len(linhas)} pares, {rodadas} rodada(s) por par. "
            "Gerado por `python manage.py comparar_prompts`.\n\n"
            "| Versão | Erro médio vs. referência | Faixa certa (alta/média/baixa) | Variação entre rodadas | Falhas |\n"
            "| --- | --- | --- | --- | --- |\n"
            + "\n".join(
                f"| {v} | {m['erro_medio']} pontos | {m['acerto_faixa']} | {m['variacao_media']} pontos | {m['falhas']} |"
                for v, m in resumo.items()
            )
            + "\n\n## Notas por par (uma por rodada)\n\n"
            + tabela(linhas, versoes)
            + "\n"
        )
        Path(saida).write_text(texto, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Resultado em {saida}"))
        return None
