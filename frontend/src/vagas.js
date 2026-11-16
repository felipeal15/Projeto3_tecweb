// Coisas de vaga usadas em várias telas: status do kanban, nível da nota e datas.

// Colunas do kanban, na ordem. Os valores são os mesmos do backend (Vaga.Status).
export const STATUS = [
  { valor: "interessado", rotulo: "Interessado", ponto: "bg-slate-400", selo: "bg-slate-200/70 text-slate-700" },
  { valor: "candidatado", rotulo: "Candidatado", ponto: "bg-blue-500", selo: "bg-blue-50 text-blue-700" },
  { valor: "entrevista", rotulo: "Entrevista", ponto: "bg-amber-500", selo: "bg-amber-50 text-amber-700" },
  { valor: "oferta", rotulo: "Oferta", ponto: "bg-emerald-500", selo: "bg-emerald-50 text-emerald-700" },
  { valor: "encerrada", rotulo: "Encerrada", ponto: "bg-rose-500", selo: "bg-rose-50 text-rose-700" },
];

export function rotuloStatus(valor) {
  return STATUS.find((status) => status.valor === valor)?.rotulo ?? valor;
}

// Nota de aderência (0 a 100): Alta a partir de 75, Média a partir de 50.
export const NOTA_ALTA = 75;

export function nivelNota(nota) {
  if (nota >= NOTA_ALTA) {
    return { rotulo: "Alta", texto: "text-emerald-700", fundo: "bg-emerald-50", barra: "bg-emerald-500" };
  }
  if (nota >= 50) {
    return { rotulo: "Média", texto: "text-amber-700", fundo: "bg-amber-50", barra: "bg-amber-500" };
  }
  return { rotulo: "Baixa", texto: "text-rose-700", fundo: "bg-rose-50", barra: "bg-rose-500" };
}

const formatoRelativo = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });
const UNIDADES = [
  ["year", 365 * 24 * 3600],
  ["month", 30 * 24 * 3600],
  ["week", 7 * 24 * 3600],
  ["day", 24 * 3600],
  ["hour", 3600],
  ["minute", 60],
];

/** "há 2 dias", "ontem", "há 5 minutos"... */
export function tempoRelativo(dataIso) {
  const segundos = (new Date(dataIso).getTime() - Date.now()) / 1000;
  for (const [unidade, tamanho] of UNIDADES) {
    if (Math.abs(segundos) >= tamanho) {
      return formatoRelativo.format(Math.round(segundos / tamanho), unidade);
    }
  }
  return "agora há pouco";
}

/** "16/11/2026" */
export function dataCurta(dataIso) {
  return new Date(dataIso).toLocaleDateString("pt-BR");
}
