import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { lerErros } from "../api";
import { useAuth } from "../auth/useAuth";
import { AvisoErro, BotaoPrimario, CampoTexto } from "../components/Formulario";
import Logo from "../components/Logo";
import PainelMarca from "../components/PainelMarca";
import TelaCarregando from "../components/TelaCarregando";

export default function Login() {
  const { usuario, carregando, entrar } = useAuth();
  const local = useLocation();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState({ geral: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  if (carregando) return <TelaCarregando />;
  // Já logado (ou acabou de entrar): volta para a página que pediu login, ou para as vagas.
  if (usuario) return <Navigate to={local.state?.de || "/vagas"} replace />;

  async function aoEnviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErros({ geral: "", campos: {} });
    try {
      await entrar(email, senha);
    } catch (erro) {
      setErros(lerErros(erro));
      setEnviando(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <PainelMarca />

      <main className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Logo fundoEscuro={false} />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 className="text-xl font-semibold text-slate-900">Entrar</h2>
            <p className="mt-1 text-sm text-slate-500">Que bom te ver de novo.</p>

            <form onSubmit={aoEnviar} className="mt-6 space-y-4">
              <AvisoErro>{erros.geral}</AvisoErro>
              <CampoTexto
                id="email"
                rotulo="E-mail"
                type="email"
                autoComplete="email"
                placeholder="maria.silva@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                erro={erros.campos.email}
                required
              />
              <CampoTexto
                id="senha"
                rotulo="Senha"
                type="password"
                autoComplete="current-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                erro={erros.campos.senha}
                required
              />
              <BotaoPrimario
                type="submit"
                className="w-full"
                carregando={enviando}
                textoCarregando="Entrando..."
              >
                Entrar
              </BotaoPrimario>
            </form>

            <p className="mt-6 border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
              Não tem conta?{" "}
              <Link to="/cadastro" className="font-medium text-blue-600 hover:underline">
                Criar conta
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
