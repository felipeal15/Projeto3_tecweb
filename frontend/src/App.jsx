import { Navigate, Route, Routes } from "react-router-dom";
import RotaProtegida from "./auth/RotaProtegida";
import Layout from "./components/Layout";
import AnaliseVaga from "./pages/AnaliseVaga";
import Cadastro from "./pages/Cadastro";
import Curriculo from "./pages/Curriculo";
import Login from "./pages/Login";
import MinhasVagas from "./pages/MinhasVagas";
import NovaVaga from "./pages/NovaVaga";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/cadastro" element={<Cadastro />} />

      {/* Tudo aqui dentro exige login e aparece com o menu lateral. */}
      <Route element={<RotaProtegida />}>
        <Route element={<Layout />}>
          <Route path="/vagas" element={<MinhasVagas />} />
          <Route path="/vagas/:id" element={<AnaliseVaga />} />
          <Route path="/nova-vaga" element={<NovaVaga />} />
          <Route path="/curriculo" element={<Curriculo />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/vagas" replace />} />
    </Routes>
  );
}
