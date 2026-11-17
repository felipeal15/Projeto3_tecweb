// Opções e textos das preferências, usados na tela de preferências, no filtro do kanban
// e nas sugestões de busca. Os valores de TIPOS e MODALIDADES são os mesmos do backend.

export const AREAS_SUGERIDAS = ["Dados", "Desenvolvimento web", "Produto", "Finanças", "Design"];

export const STACK_SUGERIDA = ["Python", "SQL", "React", "Django", "Java", "JavaScript", "Power BI"];

export const TIPOS = [
  { valor: "estagio", rotulo: "Estágio" },
  { valor: "trainee", rotulo: "Trainee" },
  { valor: "junior", rotulo: "Júnior" },
];

export const MODALIDADES = [
  { valor: "presencial", rotulo: "Presencial" },
  { valor: "hibrido", rotulo: "Híbrido" },
  { valor: "remoto", rotulo: "Remoto" },
];

export const PREFERENCIAS_VAZIAS = {
  areas: [],
  tipos: [],
  modalidades: [],
  cidade: "",
  stack: [],
  evitar: "",
  atualizado_em: null,
};

function rotulos(opcoes, valores) {
  return opcoes.filter((opcao) => valores.includes(opcao.valor)).map((opcao) => opcao.rotulo);
}

/** "Híbrido ou remoto" a partir de ["hibrido", "remoto"]. */
function juntarComOu(lista) {
  if (lista.length === 0) return "";
  const [primeiro, ...resto] = lista;
  return [primeiro, ...resto.map((item) => item.toLowerCase())].join(" ou ");
}

/** "São Paulo, SP" -> "São Paulo" (igual ao backend, que compara só a cidade). */
export function nomeDaCidade(cidade = "") {
  return cidade.split(/[,/(]| - /)[0].trim();
}

/** O filtro do kanban só usa tipo, modalidade e cidade (o resto vai para a IA). */
export function temFiltro(preferencias) {
  return Boolean(
    preferencias &&
      (preferencias.tipos.length || preferencias.modalidades.length || preferencias.cidade.trim()),
  );
}

/** Chips do filtro do kanban: ["Estágio", "Híbrido ou remoto", "São Paulo"]. */
export function chipsDoFiltro(preferencias) {
  return [
    juntarComOu(rotulos(TIPOS, preferencias.tipos)),
    juntarComOu(rotulos(MODALIDADES, preferencias.modalidades)),
    nomeDaCidade(preferencias.cidade),
  ].filter(Boolean);
}

/** Chips de "Com base em" nas sugestões: filtro + áreas + stack. */
export function resumoDasPreferencias(preferencias) {
  return [
    ...chipsDoFiltro(preferencias),
    ...preferencias.areas,
    preferencias.stack.join(" · "),
  ].filter(Boolean);
}
