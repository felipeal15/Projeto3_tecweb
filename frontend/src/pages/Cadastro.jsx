import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { lerErros } from "../api";
import { useAuth } from "../auth/useAuth";
import AvisoPrivacidade from "../components/AvisoPrivacidade";
import { AvisoErro, BotaoPrimario, CampoTexto } from "../components/Formulario";
import Logo from "../components/Logo";
import PainelMarca from "../components/PainelMarca";
import PassosOnboarding from "../components/PassosOnboarding";
import TelaCarregando from "../components/TelaCarregando";

export default function Cadastro() {
  const { usuario, carregando, cadastrar } = useAuth();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState({ geral: "", campos: {} });
  const [enviando, setEnviando] = useState(false);
  const [criouAgora, setCriouAgora] = useState(false);

  if (carregando) return <TelaCarregando />;
  // Conta nova segue o onboarding (passo 2: currículo); quem já estava logado vai para as vagas.
  if (usuario) return <Navigate to={criouAgora ? "/curriculo" : "/vagas"} replace />;

  async function aoEnviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErros({ geral: "", campos: {} });
    setCriouAgora(true);
    try {
      await cadastrar(nome, email, senha);
    } catch (erro) {
      setCriouAgora(false);
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
            <PassosOnboarding atual={0} />
            <h2 className="mt-5 text-xl font-semibold text-slate-900">Criar conta</h2>
            <p className="mt-1 text-sm text-slate-500">Leva menos de 1 minuto.</p>

            <form onSubmit={aoEnviar} className="mt-6 space-y-4">
              <AvisoErro>{erros.geral}</AvisoErro>
              <CampoTexto
                id="nome"
                rotulo="Nome completo"
                autoComplete="name"
                placeholder="Maria Silva"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                erro={erros.campos.nome}
                required
              />
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
                autoComplete="new-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                erro={erros.campos.senha}
                dica="Mínimo de 8 caracteres."
                minLength={8}
                required
              />

              <AvisoPrivacidade curto />

              <BotaoPrimario
                type="submit"
                className="w-full"
                carregando={enviando}
                textoCarregando="Criando conta..."
              >
                Criar conta e continuar
              </BotaoPrimario>
            </form>

            <p className="mt-6 border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
              Já tem conta?{" "}
              <Link to="/login" className="font-medium text-blue-600 hover:underline">
                Entrar
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
