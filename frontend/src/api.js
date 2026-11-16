import axios from "axios";

export const CHAVE_TOKEN = "encaixe:token";

// Use este `api` em vez do axios direto: ele já sabe o endereço do backend
// e manda o token do usuário logado. Ex.: api.get("/vagas/"), api.patch(`/vagas/${id}/`, { status }).
// As rotas do Django terminam com barra: "/vagas/", não "/vagas".
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(CHAVE_TOKEN);
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Token inválido ou apagado (401): esquece o login e avisa o AuthProvider,
// que manda o usuário de volta para a tela de login.
api.interceptors.response.use(
  (resposta) => resposta,
  (erro) => {
    if (erro.response?.status === 401 && localStorage.getItem(CHAVE_TOKEN)) {
      localStorage.removeItem(CHAVE_TOKEN);
      window.dispatchEvent(new Event("encaixe:sessao-expirada"));
    }
    return Promise.reject(erro);
  },
);

// Tempo máximo das chamadas que usam a IA (análise, carta, currículo). O Gemini leva
// de 5 a 30 s e o backend ainda tenta de novo se ele falhar. Use: api.post(url, dados, { timeout: TEMPO_IA }).
export const TEMPO_IA = 120000;

/**
 * Transforma um erro do axios em mensagens para a tela.
 * O DRF devolve { campo: ["mensagem"] } para erros de campo
 * e { detail } ou { non_field_errors } para erros gerais.
 * Falhas da IA (502) trazem também { codigo }: limite, tempo_esgotado, formato_invalido...
 */
export function lerErros(erro) {
  if (!erro.response) {
    if (erro.code === "ECONNABORTED" || erro.code === "ETIMEDOUT") {
      return {
        geral: "O servidor demorou demais para responder. Tente de novo.",
        campos: {},
        codigo: "tempo_esgotado",
      };
    }
    return { geral: "Não foi possível falar com o servidor. Ele está rodando?", campos: {} };
  }
  const dados = erro.response.data;
  if (!dados || typeof dados !== "object") {
    const geral =
      erro.response.status >= 500
        ? "O servidor teve um problema. Tente de novo em instantes."
        : "Algo deu errado. Tente de novo.";
    return { geral, campos: {} };
  }
  const campos = {};
  let geral = "";
  for (const [chave, valor] of Object.entries(dados)) {
    if (chave === "codigo") continue;
    const texto = Array.isArray(valor) ? valor.join(" ") : String(valor);
    if (chave === "detail" || chave === "non_field_errors") {
      geral = texto;
    } else {
      campos[chave] = texto;
    }
  }
  return { geral, campos, codigo: dados.codigo };
}

export default api;
