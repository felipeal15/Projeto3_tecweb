import { useEffect, useState } from "react";
import api, { CHAVE_TOKEN } from "../api";
import { AuthContext } from "./AuthContext";

export default function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  // Se já existe um token salvo, ainda não sabemos se ele vale: confere no backend.
  const [carregando, setCarregando] = useState(() =>
    Boolean(localStorage.getItem(CHAVE_TOKEN)),
  );

  useEffect(() => {
    if (!localStorage.getItem(CHAVE_TOKEN)) return;
    api
      .get("/auth/eu/")
      .then((res) => setUsuario(res.data))
      .catch(() => {
        // 401 já apagou o token (ver api.js); sem servidor, o usuário entra de novo.
      })
      .finally(() => setCarregando(false));
  }, []);

  useEffect(() => {
    const aoExpirar = () => setUsuario(null);
    window.addEventListener("encaixe:sessao-expirada", aoExpirar);
    return () => window.removeEventListener("encaixe:sessao-expirada", aoExpirar);
  }, []);

  function guardarSessao({ token, usuario }) {
    localStorage.setItem(CHAVE_TOKEN, token);
    setUsuario(usuario);
  }

  async function entrar(email, senha) {
    const res = await api.post("/auth/login/", { email, senha });
    guardarSessao(res.data);
  }

  async function cadastrar(nome, email, senha) {
    const res = await api.post("/auth/cadastro/", { nome, email, senha });
    guardarSessao(res.data);
  }

  async function sair() {
    try {
      await api.post("/auth/logout/");
    } catch {
      // Mesmo se o backend não responder, o usuário sai neste navegador.
    }
    localStorage.removeItem(CHAVE_TOKEN);
    setUsuario(null);
  }

  return (
    <AuthContext.Provider value={{ usuario, carregando, entrar, cadastrar, sair }}>
      {children}
    </AuthContext.Provider>
  );
}
