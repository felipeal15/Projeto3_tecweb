import {
  CircleCheck,
  ExternalLink,
  Lightbulb,
  PenLine,
  RefreshCw,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import api, { lerErros, TEMPO_IA } from "../api";
import Cabecalho from "../components/Cabecalho";
import CarregandoIA from "../components/CarregandoIA";
import { AvisoErro, Botao, LinkBotao } from "../components/Formulario";
import { SeloIA } from "../components/Selos";
import TelaCarregando from "../components/TelaCarregando";
import { nivelNota, rotuloStatus, STATUS, tempoRelativo } from "../vagas";

// Rota /vagas/:id. Mostra a vaga e a última análise (GET /api/vagas/<id>/analise/).
// POST no mesmo endereço pede a análise à IA (o backend devolve do cache se nada mudou).
export default function AnaliseVaga() {
  const { id } = useParams();
  const local = useLocation();
  const navegar = useNavigate();

  const [vaga, setVaga] = useState(null);
  const [analise, setAnalise] = useState(null);
  const [temCurriculo, setTemCurriculo] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erroCarregar, setErroCarregar] = useState("");
  const [analisando, setAnalisando] = useState(false);
  const [erroIA, setErroIA] = useState("");
  const [erroStatus, setErroStatus] = useState("");
  // Veio da tela "Nova vaga" pelo botão "Analisar com IA": analisa assim que carregar.
  const analisarAoAbrir = useRef(Boolean(local.state?.analisar));

  const analisar = useCallback(async () => {
    setAnalisando(true);
    setErroIA("");
    try {
      const { data } = await api.post(`/vagas/${id}/analise/`, null, { timeout: TEMPO_IA });
      setAnalise(data);
      setVaga((atual) => atual && { ...atual, ultima_nota: data.nota });
    } catch (erro) {
      setErroIA(lerErros(erro).geral);
    } finally {
      setAnalisando(false);
    }
  }, [id]);

  // Busca a vaga, a análise e se existe currículo. Devolve a função que ignora a resposta
  // (o efeito chama ao sair da página, para não mexer no estado de uma tela que já fechou).
  const buscar = useCallback(() => {
    let ativo = true;
    const seNaoExiste = (valor) => (erro) =>
      erro.response?.status === 404 ? valor : Promise.reject(erro);

    Promise.all([
      api.get(`/vagas/${id}/`),
      api.get(`/vagas/${id}/analise/`).catch(seNaoExiste({ data: null })),
      api
        .get("/curriculo/")
        .then(() => true)
        .catch(seNaoExiste(false)),
    ])
      .then(([respostaVaga, respostaAnalise, curriculo]) => {
        if (!ativo) return;
        setVaga(respostaVaga.data);
        setAnalise(respostaAnalise.data);
        setTemCurriculo(curriculo);
        if (analisarAoAbrir.current) {
          analisarAoAbrir.current = false;
          if (curriculo) analisar();
        }
      })
      .catch((erro) => {
        if (!ativo) return;
        setErroCarregar(
          erro.response?.status === 404 ? "Vaga não encontrada." : lerErros(erro).geral,
        );
      })
      .finally(() => ativo && setCarregando(false));

    return () => {
      ativo = false;
    };
  }, [id, analisar]);

  useEffect(() => buscar(), [buscar]);

  function tentarDeNovo() {
    setCarregando(true);
    setErroCarregar("");
    buscar();
  }

  // Tira o pedido de análise do histórico, para não analisar de novo ao recarregar a página.
  useEffect(() => {
    if (local.state?.analisar) navegar(local.pathname, { replace: true, state: null });
  }, [local, navegar]);

  async function mudarStatus(evento) {
    const status = evento.target.value;
    const anterior = vaga.status;
    setErroStatus("");
    setVaga((atual) => ({ ...atual, status }));
    try {
      await api.patch(`/vagas/${id}/`, { status });
    } catch (erro) {
      setVaga((atual) => ({ ...atual, status: anterior }));
      setErroStatus(`Não foi possível mudar o status. ${lerErros(erro).geral}`);
    }
  }

  if (carregando && !vaga) return <TelaCarregando dentroDoLayout />;

  if (erroCarregar) {
    return (
      <section>
        <Cabecalho voltar={{ para: "/vagas", rotulo: "Minhas vagas" }} titulo="Análise da vaga" />
        <AvisoErro aoTentarDeNovo={erroCarregar === "Vaga não encontrada." ? undefined : tentarDeNovo}>
          {erroCarregar}
        </AvisoErro>
      </section>
    );
  }

  const subtitulo = [
    analise ? `Analisada ${tempoRelativo(analise.criado_em)}` : "Ainda não analisada",
    vaga.local,
    `status: ${rotuloStatus(vaga.status)}`,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <section>
      <Cabecalho
        voltar={{ para: "/vagas", rotulo: "Minhas vagas" }}
        titulo={`${vaga.titulo} · ${vaga.empresa}`}
        subtitulo={subtitulo}
      >
        <label htmlFor="status" className="sr-only">
          Status da vaga
        </label>
        <select
          id="status"
          value={vaga.status}
          onChange={mudarStatus}
          className="cursor-pointer rounded-lg border border-slate-300 bg-white py-2.5 pr-8 pl-3 text-sm font-medium text-slate-700 shadow-xs outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-600/20"
        >
          {STATUS.map((status) => (
            <option key={status.valor} value={status.valor}>
              {status.rotulo}
            </option>
          ))}
        </select>
        <LinkBotao para={`/vagas/${id}/carta`} variante="ia">
          <PenLine className="size-4" aria-hidden="true" />
          Carta de apresentação
        </LinkBotao>
      </Cabecalho>

      <div className="space-y-4">
        {erroStatus && <AvisoErro>{erroStatus}</AvisoErro>}
        {erroIA && !analisando && <AvisoErro aoTentarDeNovo={analisar}>{erroIA}</AvisoErro>}

        {analisando ? (
          <CarregandoIA
            titulo="Analisando a vaga com a IA"
            descricao="A IA está lendo os requisitos da vaga e comparando com o seu currículo."
          />
        ) : analise ? (
          <>
            {analise.desatualizada && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                <span className="flex items-center gap-2">
                  <TriangleAlert className="size-4 shrink-0" aria-hidden="true" />
                  Seu currículo ou a vaga mudou depois desta análise.
                </span>
                <Botao variante="secundario" onClick={analisar} className="py-1.5">
                  <RefreshCw className="size-4" aria-hidden="true" />
                  Analisar de novo
                </Botao>
              </div>
            )}
            <ResultadoAnalise analise={analise} vaga={vaga} />
          </>
        ) : (
          <SemAnalise temCurriculo={temCurriculo} aoAnalisar={analisar} vaga={vaga} />
        )}
      </div>
    </section>
  );
}

function ResultadoAnalise({ analise, vaga }) {
  const { resultado } = analise;
  const nivel = nivelNota(analise.nota);

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="space-y-6">
        <div className="flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:flex-row sm:items-center sm:p-6">
          <div className="shrink-0 sm:w-40">
            <p className={`text-5xl font-bold tracking-tight ${nivel.texto}`}>{analise.nota}%</p>
            <p className={`mt-1 text-sm font-semibold ${nivel.texto}`}>{nivel.rotulo} aderência</p>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-slate-900">Resumo</h2>
              <SeloIA />
            </div>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{resultado.resumo}</p>
            <div
              className="mt-4 h-2 rounded-full bg-slate-100"
              role="meter"
              aria-label="Aderência"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={analise.nota}
            >
              <div className={`h-full rounded-full ${nivel.barra}`} style={{ width: `${analise.nota}%` }} />
            </div>
          </div>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <ListaResultado
            titulo="Requisitos atendidos"
            itens={resultado.requisitos_atendidos}
            vazio="A IA não encontrou no currículo nenhum requisito da vaga."
            Icone={CircleCheck}
            corIcone="text-emerald-600"
            corPonto="bg-emerald-500"
            corContador="bg-emerald-50 text-emerald-700"
          />
          <ListaResultado
            titulo="Lacunas"
            itens={resultado.lacunas}
            vazio="Nenhuma lacuna: o currículo cobre o que a vaga pede."
            Icone={TriangleAlert}
            corIcone="text-amber-500"
            corPonto="bg-amber-500"
            corContador="bg-amber-50 text-amber-700"
          />
        </div>

        <DescricaoVaga vaga={vaga} />
      </div>

      <aside className="space-y-4">
        <div className="rounded-xl border border-violet-200 bg-violet-50/70 p-5">
          <div className="flex items-start justify-between gap-2">
            <h2 className="font-semibold text-slate-900">Sugestões para a candidatura</h2>
            <SeloIA />
          </div>
          {resultado.sugestoes.length ? (
            <ul className="mt-4 space-y-2.5">
              {resultado.sugestoes.map((sugestao, indice) => (
                <li
                  key={indice}
                  className="flex gap-2.5 rounded-lg border border-violet-100 bg-white p-3 text-sm leading-relaxed text-slate-700"
                >
                  <Lightbulb className="mt-0.5 size-4 shrink-0 text-violet-500" aria-hidden="true" />
                  {sugestao}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-600">A IA não teve sugestões para esta vaga.</p>
          )}
        </div>
        <p className="px-1 text-xs leading-relaxed text-slate-500">
          A IA pode errar: confira os pontos com o texto da vaga. Modelo {analise.modelo_ia} · prompt{" "}
          {analise.versao_prompt}.
        </p>
      </aside>
    </div>
  );
}

function ListaResultado({ titulo, itens, vazio, Icone, corIcone, corPonto, corContador }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900">
          <Icone className={`size-4 ${corIcone}`} aria-hidden="true" />
          {titulo}
        </h2>
        <span className={`rounded-md px-1.5 py-0.5 text-xs font-semibold ${corContador}`}>
          {itens.length}
        </span>
      </div>
      {itens.length ? (
        <ul className="mt-4 space-y-2.5">
          {itens.map((item, indice) => (
            <li key={indice} className="flex gap-2.5 text-sm leading-relaxed text-slate-700">
              <span className={`mt-2 size-1.5 shrink-0 rounded-full ${corPonto}`} aria-hidden="true" />
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{vazio}</p>
      )}
    </div>
  );
}

function DescricaoVaga({ vaga }) {
  return (
    <details className="group rounded-xl border border-slate-200 bg-white shadow-xs">
      <summary className="flex cursor-pointer items-center justify-between gap-3 px-5 py-4 text-sm font-semibold text-slate-900 select-none">
        Descrição da vaga
        <span className="text-xs font-medium text-blue-600 group-open:hidden">Mostrar</span>
        <span className="hidden text-xs font-medium text-blue-600 group-open:inline">Esconder</span>
      </summary>
      <div className="border-t border-slate-100 px-5 py-4">
        {vaga.link && (
          <a
            href={vaga.link}
            target="_blank"
            rel="noreferrer"
            className="mb-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:underline"
          >
            Ver anúncio original
            <ExternalLink className="size-3.5" aria-hidden="true" />
          </a>
        )}
        <p className="text-sm leading-relaxed whitespace-pre-line text-slate-700">{vaga.descricao}</p>
      </div>
    </details>
  );
}

function SemAnalise({ temCurriculo, aoAnalisar, vaga }) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
        <Sparkles className="mx-auto size-8 text-violet-400" aria-hidden="true" />
        <h2 className="mt-3 font-semibold text-slate-900">Esta vaga ainda não foi analisada</h2>
        {temCurriculo === false ? (
          <>
            <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
              Para a IA comparar a vaga com você, cadastre primeiro o seu currículo.
            </p>
            <LinkBotao para="/curriculo" className="mt-5">
              Cadastrar currículo
            </LinkBotao>
          </>
        ) : (
          <>
            <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
              A IA compara a vaga com o seu currículo e mostra a nota de aderência, as lacunas e
              sugestões.
            </p>
            <Botao variante="ia" onClick={aoAnalisar} className="mt-5">
              <Sparkles className="size-4" aria-hidden="true" />
              Analisar com IA
            </Botao>
            <p className="mt-3 text-xs text-slate-400">
              O texto do currículo e da vaga vai para a API do Google Gemini.{" "}
              <Link to="/curriculo" className="underline">
                Saiba mais
              </Link>
            </p>
          </>
        )}
      </div>
      <DescricaoVaga vaga={vaga} />
    </div>
  );
}
