import { Navigate, Outlet, useLocation } from "react-router-dom";
import TelaCarregando from "../components/TelaCarregando";
import { useAuth } from "./useAuth";

/** Envolve as rotas que exigem login. Sem login, vai para /login e volta depois. */
export default function RotaProtegida() {
  const { usuario, carregando } = useAuth();
  const local = useLocation();

  if (carregando) return <TelaCarregando />;
  if (!usuario) {
    return <Navigate to="/login" replace state={{ de: local.pathname }} />;
  }
  return <Outlet />;
}
