import { useContext } from "react";
import { AuthContext } from "./AuthContext";

/**
 * Dá acesso ao login em qualquer componente:
 * const { usuario, entrar, cadastrar, sair } = useAuth();
 * `usuario` é { id, nome, email } ou null se ninguém estiver logado.
 */
export function useAuth() {
  return useContext(AuthContext);
}
