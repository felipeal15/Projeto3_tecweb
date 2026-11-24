# Comparação de prompts da análise: v2 × v3

Modelo `gemini-3.5-flash-lite`, 11 pares, 2 rodada(s) por par. Gerado por `python manage.py comparar_prompts`.

| Versão | Erro médio vs. referência | Faixa certa (alta/média/baixa) | Variação entre rodadas | Falhas |
| --- | --- | --- | --- | --- |
| v2 | 10.7 pontos | 10/11 | 2.5 pontos | 1 |
| v3 | 12.7 pontos | 10/11 | 1.4 pontos | 4 |

## Notas por par (uma por rodada)

| Par | Vaga | Referência | v2 | v3 |
| --- | --- | --- | --- | --- |
| 1 | ana × Estágio em Dados | 85 | 90 / 85 | erro / 95 |
| 2 | ana × Desenvolvedor Back-end Júnior | 25 | erro / 10 | 15 / 10 |
| 3 | ana × Estágio em Engenharia de Software | 65 | 80 / 80 | 90 / 90 |
| 4 | bruno × Estágio em FP&A | 85 | 95 / 95 | 95 / 95 |
| 5 | bruno × Estágio em Ciência de Dados | 20 | 10 / 10 | 15 / erro |
| 6 | bruno × Trainee de Operações e Supply Chain | 60 | 70 / 60 | 70 / erro |
| 7 | carla × Desenvolvedora Front-end Júnior | 90 | 95 / 90 | 95 / 95 |
| 8 | carla × Engenheiro de Dados Júnior | 40 | 10 / 15 | 15 / 15 |
| 9 | diego × Estágio em UX/UI Design | 85 | 80 / 80 | 75 / erro |
| 10 | diego × Estágio em Desenvolvimento Front-end | 25 | 15 / 15 | 15 / 15 |
| 11 | diego × Estágio em Marketing Digital | 55 | 70 / 70 | 75 / 70 |
