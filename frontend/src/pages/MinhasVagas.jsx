import { BriefcaseBusiness, CircleCheck, Ellipsis, Funnel, MoveRight, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api, { lerErros } from "../api";
import Cabecalho from "../components/Cabecalho";
import { AvisoErro, Botao, LinkBotao } from "../components/Formulario";
import { SeloNota } from "../components/Selos";
import { chipsDoFiltro, temFiltro } from "../preferencias";
import { NOTA_ALTA, STATUS, tempoRelativo } from "../vagas";

// O filtro por preferências fica lembrado neste navegador.
const CHAVE_FILTRO = "encaixe:filtrar-preferencias";

function lerFiltroSalvo() {
  try {
    return localStorage.getItem(CHAVE_FILTRO) === "1";
  } catch {
    return false;
  }
}

function salvarFiltro(ativo) {
  try {
    localStorage.setItem(CHAVE_FILTRO, ativo ? "1" : "0");
  } catch {
    // Sem localStorage (aba anônima bloqueada): o filtro só não fica lembrado.
  }
}

// Kanban: GET /api/vagas/ lista; PATCH /api/vagas/<id>/ com { status } muda de coluna.
// Dá para mover arrastando o card ou pelo menu "⋯" do card (que funciona no celular e no teclado).
export default function MinhasVagas() {
  const [vagas, setVagas] = useState(null); // null = carregando
  const [erroCarregar, setErroCarregar] = useState("");
  const [erroAcao, setErroAcao] = useState("");
  const [arrastando, setArrastando] = useState(null); // id da vaga sendo arrastada
  const [colunaAlvo, setColunaAlvo] = useState(null);
  // Filtro por preferências: o backend manda em cada vaga o que ela tem fora das preferências.
  const [preferencias, setPreferencias] = useState(null);
  const [filtrando, setFiltrando] = useState(lerFiltroSalvo);

  const buscar = useCallback(() => {
    api
      .get("/vagas/")
      .then(({ data }) => setVagas(data))
      .catch((erro) => setErroCarregar(lerErros(erro).geral));
    api
      .get("/preferencias/")
      .then(({ data }) => setPreferencias(data))
      .catch(() => setPreferencias(null)); // sem preferências, o quadro funciona sem filtro
  }, []);

  function alternarFiltro(ativo) {
    setFiltrando(ativo);
    salvarFiltro(ativo);
  }

  useEffect(() => {
    buscar();
  }, [buscar]);

  function tentarDeNovo() {
    setErroCarregar("");
    buscar();
  }

  async function mover(vaga, status) {
    if (vaga.status === status) return;
    setErroAcao("");
    // Atualiza na tela antes da resposta (o card vai para o topo, como na ordem do backend).
    setVagas((lista) => [{ ...vaga, status }, ...lista.filter((v) => v.id !== vaga.id)]);
    try {
      const { data } = await api.patch(`/vagas/${vaga.id}/`, { status });
      setVagas((lista) => lista.map((v) => (v.id === data.id ? data : v)));
    } catch (erro) {
      setVagas((lista) => lista.map((v) => (v.id === vaga.id ? vaga : v)));
      setErroAcao(`Não foi possível mover "${vaga.titulo}". ${lerErros(erro).geral}`);
    }
  }

  async function apagar(vaga) {
    if (!window.confirm(`Excluir a vaga "${vaga.titulo} · ${vaga.empresa}"? A análise e a carta também serão apagadas.`)) {
      return;
    }
    setErroAcao("");
    try {
      await api.delete(`/vagas/${vaga.id}/`);
      setVagas((lista) => lista.filter((v) => v.id !== vaga.id));
    } catch (erro) {
      setErroAcao(`Não foi possível excluir "${vaga.titulo}". ${lerErros(erro).geral}`);
    }
  }

  function soltarEm(status) {
    const vaga = vagas.find((v) => v.id === arrastando);
    setArrastando(null);
    setColunaAlvo(null);
    if (vaga) mover(vaga, status);
  }

  if (erroCarregar) {
    return (
      <section>
        <Cabecalho titulo="Minhas vagas" />
        <AvisoErro aoTentarDeNovo={tentarDeNovo}>{erroCarregar}</AvisoErro>
      </section>
    );
  }

  const altas = vagas?.filter((v) => v.ultima_nota >= NOTA_ALTA).length ?? 0;
  const subtitulo = vagas
    ? `${vagas.length} ${vagas.length === 1 ? "vaga salva" : "vagas salvas"} · ${altas} com alta aderência`
    : "Carregando suas vagas...";

  const podeFiltrar = temFiltro(preferencias);
  const filtroAtivo = filtrando && podeFiltrar;
  const visiveis =
    vagas && filtroAtivo ? vagas.filter((v) => !v.fora_das_preferencias?.length) : vagas;
  const escondidas = vagas ? vagas.length - visiveis.length : 0;

  return (
    <section>
      <Cabecalho titulo="Minhas vagas" subtitulo={subtitulo}>
        {preferencias &&
          (podeFiltrar ? (
            <Botao
              variante="secundario"
              aria-pressed={filtroAtivo}
              onClick={() => alternarFiltro(!filtroAtivo)}
            >
              <Funnel className="size-4" aria-hidden="true" />
              Filtrar por preferências
              {filtroAtivo && <span className="size-1.5 rounded-full bg-blue-600" aria-hidden="true" />}
            </Botao>
          ) : (
            <LinkBotao
              para="/preferencias"
              variante="secundario"
              title="Defina tipo de vaga, modalidade ou cidade para filtrar o quadro"
            >
              <Funnel className="size-4" aria-hidden="true" />
              Filtrar por preferências
            </LinkBotao>
          ))}
        <LinkBotao para="/nova-vaga">
          <Plus className="size-4" aria-hidden="true" />
          Nova vaga
        </LinkBotao>
      </Cabecalho>

      {filtroAtivo && (
        <div className="-mt-2 mb-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-600">Filtros:</span>
          {chipsDoFiltro(preferencias).map((chip) => (
            <span
              key={chip}
              className="inline-flex items-center gap-1.5 rounded-full border border-blue-600 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700"
            >
              <CircleCheck className="size-3.5" aria-hidden="true" />
              {chip}
            </span>
          ))}
          <button
            type="button"
            onClick={() => alternarFiltro(false)}
            className="cursor-pointer font-medium text-blue-600 hover:underline"
          >
            Limpar
          </button>
          <span className="text-xs text-slate-500" role="status">
            {escondidas > 0
              ? `· ${escondidas} ${escondidas === 1 ? "vaga escondida" : "vagas escondidas"} por não combinar`
              : "· todas as vagas combinam"}
          </span>
        </div>
      )}

      {erroAcao && (
        <div className="mb-4">
          <AvisoErro>{erroAcao}</AvisoErro>
        </div>
      )}

      {vagas === null ? (
        <QuadroCarregando />
      ) : vagas.length === 0 ? (
        <SemVagas />
      ) : (
        <>
          {/* No celular o quadro rola para o lado; no computador as 5 colunas cabem.
              `relative` prende os elementos absolutos (sr-only) dentro da rolagem; sem ele a página toda alarga. */}
          <div className="relative -mx-4 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0">
            <div className="grid auto-cols-[minmax(13rem,1fr)] grid-flow-col gap-3">
              {STATUS.map((status) => (
                <Coluna
                  key={status.valor}
                  status={status}
                  vagas={visiveis.filter((v) => v.status === status.valor)}
                  destacada={colunaAlvo === status.valor}
                  arrastando={arrastando}
                  aoEntrar={() => setColunaAlvo(status.valor)}
                  aoSair={() => setColunaAlvo((atual) => (atual === status.valor ? null : atual))}
                  aoSoltar={() => soltarEm(status.valor)}
                  aoComecarArrastar={setArrastando}
                  aoTerminarArrastar={() => {
                    setArrastando(null);
                    setColunaAlvo(null);
                  }}
                  aoMover={mover}
                  aoApagar={apagar}
                />
              ))}
            </div>
          </div>
          <p className="mt-4 flex items-start gap-2 text-xs text-slate-500">
            <MoveRight className="size-4 shrink-0" aria-hidden="true" />
            Arraste um card para outra coluna (ou use o menu ⋯ do card) para mudar o status. Clique no
            card para ver a análise.
          </p>
        </>
      )}
    </section>
  );
}

function Coluna({
  status,
  vagas,
  destacada,
  arrastando,
  aoEntrar,
  aoSair,
  aoSoltar,
  aoComecarArrastar,
  aoTerminarArrastar,
  aoMover,
  aoApagar,
}) {
  const idTitulo = `coluna-${status.valor}`;
  return (
    <section
      aria-labelledby={idTitulo}
      onDragOver={(evento) => {
        if (arrastando === null) return;
        evento.preventDefault(); // permite soltar aqui
        evento.dataTransfer.dropEffect = "move";
        if (!destacada) aoEntrar();
      }}
      onDragLeave={(evento) => {
        if (!evento.currentTarget.contains(evento.relatedTarget)) aoSair();
      }}
      onDrop={(evento) => {
        evento.preventDefault();
        aoSoltar();
      }}
      className={`flex min-h-[26rem] flex-col rounded-xl p-2.5 transition ${
        destacada ? "bg-blue-50 ring-2 ring-blue-300" : "bg-slate-100"
      }`}
    >
      <header className="flex items-center justify-between px-1 pt-0.5 pb-2.5">
        <h2
          id={idTitulo}
          className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-semibold ${status.selo}`}
        >
          <span className={`size-1.5 rounded-full ${status.ponto}`} aria-hidden="true" />
          {status.rotulo}
        </h2>
        <span className="text-xs font-medium text-slate-500">
          {vagas.length}
          <span className="sr-only"> {vagas.length === 1 ? "vaga" : "vagas"}</span>
        </span>
      </header>

      {vagas.length > 0 && (
        <ul className="flex flex-col gap-2">
          {vagas.map((vaga) => (
            <li key={vaga.id}>
              <CardVaga
                vaga={vaga}
                sendoArrastada={arrastando === vaga.id}
                aoComecarArrastar={aoComecarArrastar}
                aoTerminarArrastar={aoTerminarArrastar}
                aoMover={aoMover}
                aoApagar={aoApagar}
              />
            </li>
          ))}
        </ul>
      )}

      {vagas.length === 0 && (
        <p
          className={`rounded-lg border border-dashed px-3 py-6 text-center text-xs ${
            destacada ? "border-blue-300 text-blue-600" : "border-slate-300 text-slate-400"
          }`}
        >
          {arrastando !== null ? "Solte aqui" : "Nenhuma vaga aqui"}
        </p>
      )}

      {status.valor === "interessado" && (
        <Link
          to="/nova-vaga"
          className="mt-2 flex items-center justify-center gap-1.5 rounded-lg border border-dashed border-slate-300 px-3 py-2.5 text-sm text-slate-500 transition hover:border-slate-400 hover:bg-white hover:text-slate-700"
        >
          <Plus className="size-4" aria-hidden="true" />
          Adicionar vaga
        </Link>
      )}
    </section>
  );
}

function CardVaga({ vaga, sendoArrastada, aoComecarArrastar, aoTerminarArrastar, aoMover, aoApagar }) {
  return (
    <article
      draggable
      onDragStart={(evento) => {
        evento.dataTransfer.setData("text/plain", String(vaga.id)); // o Firefox exige algum dado
        evento.dataTransfer.effectAllowed = "move";
        aoComecarArrastar(vaga.id);
      }}
      onDragEnd={aoTerminarArrastar}
      className={`relative cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-xs transition hover:border-slate-300 hover:shadow-sm active:cursor-grabbing ${
        sendoArrastada ? "opacity-40" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm leading-snug font-semibold text-slate-900">
          {/* O link cobre o card inteiro (after:inset-0); draggable={false} deixa o card ser arrastado. */}
          <Link
            to={`/vagas/${vaga.id}`}
            draggable={false}
            className="outline-none after:absolute after:inset-0 after:rounded-lg focus-visible:after:ring-2 focus-visible:after:ring-blue-600"
          >
            {vaga.titulo}
          </Link>
        </h3>
        <MenuCard vaga={vaga} aoMover={aoMover} aoApagar={aoApagar} />
      </div>
      <p className="mt-0.5 truncate text-xs text-slate-500">
        {[vaga.empresa, vaga.local].filter(Boolean).join(" · ")}
      </p>
      <div className="mt-2.5 flex items-center justify-between gap-2">
        <SeloNota nota={vaga.ultima_nota} />
        <span className="truncate text-[11px] text-slate-400">{tempoRelativo(vaga.criado_em)}</span>
      </div>
    </article>
  );
}

const LARGURA_MENU = 208;
const ALTURA_MENU = 250;

/** Menu "⋯" do card: mover para outra coluna ou excluir. Abre por cima de tudo (position: fixed). */
function MenuCard({ vaga, aoMover, aoApagar }) {
  const [posicao, setPosicao] = useState(null); // null = fechado
  const botao = useRef(null);
  const menu = useRef(null);
  const idMenu = `menu-vaga-${vaga.id}`;

  function alternar() {
    if (posicao) {
      setPosicao(null);
      return;
    }
    const caixa = botao.current.getBoundingClientRect();
    const left = Math.max(8, Math.min(caixa.right - LARGURA_MENU, window.innerWidth - LARGURA_MENU - 8));
    const cabeEmbaixo = caixa.bottom + ALTURA_MENU < window.innerHeight;
    setPosicao(
      cabeEmbaixo
        ? { left, top: caixa.bottom + 4 }
        : { left, bottom: window.innerHeight - caixa.top + 4 },
    );
  }

  useEffect(() => {
    if (!posicao) return;
    function fechar(evento) {
      if (evento.type === "keydown" && evento.key !== "Escape") return;
      if (
        evento.type === "mousedown" &&
        (menu.current?.contains(evento.target) || botao.current?.contains(evento.target))
      ) {
        return;
      }
      setPosicao(null);
      if (evento.type === "keydown") botao.current?.focus();
    }
    document.addEventListener("mousedown", fechar);
    document.addEventListener("keydown", fechar);
    window.addEventListener("resize", fechar);
    window.addEventListener("scroll", fechar, true);
    return () => {
      document.removeEventListener("mousedown", fechar);
      document.removeEventListener("keydown", fechar);
      window.removeEventListener("resize", fechar);
      window.removeEventListener("scroll", fechar, true);
    };
  }, [posicao]);

  function escolher(acao) {
    setPosicao(null);
    acao();
  }

  return (
    <>
      <button
        ref={botao}
        type="button"
        onClick={alternar}
        aria-expanded={Boolean(posicao)}
        aria-controls={idMenu}
        aria-label={`Opções da vaga ${vaga.titulo}`}
        className="relative z-10 -mt-1 -mr-1 shrink-0 cursor-pointer rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
      >
        <Ellipsis className="size-4" aria-hidden="true" />
      </button>
      {posicao && (
        <div
          id={idMenu}
          ref={menu}
          style={{ position: "fixed", width: LARGURA_MENU, ...posicao }}
          className="z-50 rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
        >
          <p className="px-3 pt-1.5 pb-1 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Mover para
          </p>
          {STATUS.filter((status) => status.valor !== vaga.status).map((status) => (
            <button
              key={status.valor}
              type="button"
              onClick={() => escolher(() => aoMover(vaga, status.valor))}
              className="flex w-full cursor-pointer items-center gap-2 px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-50 focus-visible:bg-slate-50 focus-visible:outline-none"
            >
              <span className={`size-2 rounded-full ${status.ponto}`} aria-hidden="true" />
              {status.rotulo}
            </button>
          ))}
          <div className="my-1 border-t border-slate-100" />
          <button
            type="button"
            onClick={() => escolher(() => aoApagar(vaga))}
            className="flex w-full cursor-pointer items-center gap-2 px-3 py-1.5 text-left text-sm text-red-600 hover:bg-red-50 focus-visible:bg-red-50 focus-visible:outline-none"
          >
            <Trash2 className="size-4" aria-hidden="true" />
            Excluir vaga
          </button>
        </div>
      )}
    </>
  );
}

function QuadroCarregando() {
  return (
    <div className="grid auto-cols-[minmax(13rem,1fr)] grid-flow-col gap-3 overflow-hidden" aria-hidden="true">
      {STATUS.map((status) => (
        <div key={status.valor} className="min-h-[26rem] rounded-xl bg-slate-100 p-2.5">
          <div className="mb-3 h-5 w-24 animate-pulse rounded-md bg-slate-200" />
          <div className="h-20 animate-pulse rounded-lg bg-white" />
        </div>
      ))}
    </div>
  );
}

function SemVagas() {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
      <BriefcaseBusiness className="mx-auto size-8 text-slate-300" aria-hidden="true" />
      <h2 className="mt-3 font-semibold text-slate-900">Nenhuma vaga salva ainda</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
        Cole a descrição de uma vaga que te interessou e a IA mostra o quanto você combina com ela.
      </p>
      <LinkBotao para="/nova-vaga" className="mt-5">
        <Plus className="size-4" aria-hidden="true" />
        Adicionar primeira vaga
      </LinkBotao>
    </div>
  );
}
