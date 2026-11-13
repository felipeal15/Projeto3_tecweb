import { BriefcaseBusiness, FileText, LogOut, Plus } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import Logo from "./Logo";

// Menu lateral. Telas novas (Sugestões de busca, Vagas para você, Preferências)
// entram aqui quando forem criadas, junto com a rota no App.jsx.
const secoes = [
  {
    titulo: "Vagas",
    itens: [
      { para: "/vagas", rotulo: "Minhas vagas", Icone: BriefcaseBusiness },
      { para: "/nova-vaga", rotulo: "Nova vaga", Icone: Plus },
    ],
  },
  {
    titulo: "Perfil",
    itens: [{ para: "/curriculo", rotulo: "Currículo", Icone: FileText }],
  },
];

function iniciais(nome = "") {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  const primeira = partes[0][0];
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : "";
  return (primeira + ultima).toUpperCase();
}

function ItemMenu({ para, rotulo, Icone, compacto = false }) {
  return (
    <NavLink
      to={para}
      className={({ isActive }) =>
        `flex items-center rounded-lg py-2 text-sm font-medium whitespace-nowrap transition ${
          compacto ? "gap-1.5 px-2.5" : "gap-2.5 px-3"
        } ${
          isActive ? "bg-blue-600 text-white" : "text-blue-100/80 hover:bg-white/10 hover:text-white"
        }`
      }
    >
      <Icone className="size-4 shrink-0" aria-hidden="true" />
      {rotulo}
    </NavLink>
  );
}

function BotaoSair({ aoClicar }) {
  return (
    <button
      type="button"
      onClick={aoClicar}
      title="Sair"
      aria-label="Sair"
      className="cursor-pointer rounded-md p-2 text-blue-200/80 transition hover:bg-white/10 hover:text-white"
    >
      <LogOut className="size-4" aria-hidden="true" />
    </button>
  );
}

/** Moldura das telas logadas: menu lateral no computador, barra no topo no celular. */
export default function Layout() {
  const { usuario, sair } = useAuth();

  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden w-60 shrink-0 flex-col bg-marinho text-white md:sticky md:top-0 md:flex md:h-screen">
        <div className="px-5 py-5">
          <Logo />
        </div>

        <nav className="flex-1 space-y-6 px-3" aria-label="Menu principal">
          {secoes.map((secao) => (
            <div key={secao.titulo}>
              <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-blue-200/60 uppercase">
                {secao.titulo}
              </p>
              <ul className="space-y-1">
                {secao.itens.map((item) => (
                  <li key={item.para}>
                    <ItemMenu {...item} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="flex items-center gap-3 border-t border-white/10 px-4 py-4">
          <span className="grid size-9 shrink-0 place-items-center rounded-full bg-blue-600 text-xs font-semibold">
            {iniciais(usuario.nome)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{usuario.nome}</p>
            <p className="truncate text-xs text-blue-200/70">{usuario.email}</p>
          </div>
          <BotaoSair aoClicar={sair} />
        </div>
      </aside>

      <header className="sticky top-0 z-10 bg-marinho text-white md:hidden">
        <div className="flex items-center justify-between px-4 py-3">
          <Logo />
          <BotaoSair aoClicar={sair} />
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3" aria-label="Menu principal">
          {secoes
            .flatMap((secao) => secao.itens)
            .map((item) => (
              <ItemMenu key={item.para} {...item} compacto />
            ))}
        </nav>
      </header>

      <main className="min-w-0 flex-1 px-4 py-6 sm:px-8 sm:py-8">
        <Outlet />
      </main>
    </div>
  );
}
