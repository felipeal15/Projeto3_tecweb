import { ExternalLink, PenLine, RefreshCw, ShieldCheck, Sparkles, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { lerErros, TEMPO_IA } from "../api";
import Cabecalho from "../components/Cabecalho";
import CarregandoIA from "../components/CarregandoIA";
import { AvisoErro, Botao, LinkBotao } from "../components/Formulario";
import { SeloIA, SeloNota } from "../components/Selos";
import TelaCarregando from "../components/TelaCarregando";
import { resumoDasPreferencias } from "../preferencias";
import { tempoRelativo } from "../vagas";

// GET /api/sugestoes/ mostra as últimas sugestões; POST pede sugestões novas à IA.
// Na primeira visita (sem sugestões e com currículo), gera sozinho.
export default function SugestoesBusca() {
  const [sugestoes, setSugestoes] = useState(null);
  const [preferencias, setPreferencias] = useState(null);
  const [temCurriculo, setTemCurriculo] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erroCarregar, setErroCarregar] = useState("");
  const [gerando, setGerando] = useState(false);
  const [erroIA, setErroIA] = useState("");

  const gerar = useCallback(async () => {
    setGerando(true);
    setErroIA("");
    try {
      const { data } = await api.post("/sugestoes/", null, { timeout: TEMPO_IA });
      setSugestoes(data);
    } catch (erro) {
      setErroIA(lerErros(erro).geral);
    } finally {
      setGerando(false);
    }
  }, []);

  // Devolve a função que ignora a resposta se a página fechar antes.
  const buscar = useCallback(() => {
    let ativo = true;
    const seNaoExiste = (valor) => (erro) =>
      erro.response?.status === 404 ? valor : Promise.reject(erro);

    Promise.all([
      api.get("/sugestoes/").then(({ data }) => data).catch(seNaoExiste(null)),
      api.get("/preferencias/").then(({ data }) => data),
      api.get("/curriculo/").then(() => true).catch(seNaoExiste(false)),
    ])
      .then(([salvas, prefs, curriculo]) => {
        if (!ativo) return;
        setSugestoes(salvas);
        setPreferencias(prefs);
        setTemCurriculo(curriculo);
        if (!salvas && curriculo) gerar();
      })
      .catch((erro) => ativo && setErroCarregar(lerErros(erro).geral))
      .finally(() => ativo && setCarregando(false));

    return () => {
      ativo = false;
    };
  }, [gerar]);

  useEffect(() => buscar(), [buscar]);

  if (carregando) return <TelaCarregando dentroDoLayout />;

  if (erroCarregar) {
    return (
      <section>
        <Cabecalho titulo="Sugestões de busca" />
        <AvisoErro
          aoTentarDeNovo={() => {
            setErroCarregar("");
            setCarregando(true);
            buscar();
          }}
        >
          {erroCarregar}
        </AvisoErro>
      </section>
    );
  }

  return (
    <section>
      <Cabecalho
        titulo="Sugestões de busca"
        subtitulo="Cargos e palavras-chave que combinam com o seu currículo e as suas preferências."
      >
        {temCurriculo && (
          <Botao variante="ia" onClick={gerar} carregando={gerando} textoCarregando="Gerando...">
            {sugestoes ? (
              <RefreshCw className="size-4" aria-hidden="true" />
            ) : (
              <Sparkles className="size-4" aria-hidden="true" />
            )}
            {sugestoes ? "Atualizar sugestões" : "Gerar sugestões"}
          </Botao>
        )}
      </Cabecalho>

      <BaseadoEm preferencias={preferencias} />

      <div className="mt-6 space-y-4">
        {erroIA && !gerando && <AvisoErro aoTentarDeNovo={gerar}>{erroIA}</AvisoErro>}

        {!temCurriculo ? (
          <SemCurriculo />
        ) : gerando ? (
          <CarregandoIA
            titulo="Gerando sugestões com a IA"
            descricao="A IA está lendo o seu currículo e as suas preferências para sugerir cargos e palavras-chave."
          />
        ) : (
          sugestoes && <ListaSugestoes sugestoes={sugestoes} aoAtualizar={gerar} />
        )}
      </div>
    </section>
  );
}

function BaseadoEm({ preferencias }) {
  const chips = preferencias ? resumoDasPreferencias(preferencias) : [];
  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="text-slate-600">
        {chips.length ? "Com base em:" : "Com base só no seu currículo."}
      </span>
      {chips.map((chip) => (
        <span key={chip} className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700">
          {chip}
        </span>
      ))}
      <Link
        to="/preferencias"
        className="inline-flex items-center gap-1.5 font-medium text-blue-600 hover:underline"
      >
        <PenLine className="size-3.5" aria-hidden="true" />
        {chips.length ? "Editar preferências" : "Definir preferências"}
      </Link>
    </div>
  );
}

function ListaSugestoes({ sugestoes, aoAtualizar }) {
  return (
    <>
      {sugestoes.desatualizada && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <span className="flex items-center gap-2">
            <TriangleAlert className="size-4 shrink-0" aria-hidden="true" />
            Seu currículo ou suas preferências mudaram depois destas sugestões.
          </span>
          <Botao variante="secundario" onClick={aoAtualizar} className="py-1.5">
            <RefreshCw className="size-4" aria-hidden="true" />
            Atualizar
          </Botao>
        </div>
      )}

      <div className="flex items-center gap-2 pt-2">
        <h2 className="font-semibold text-slate-900">Cargos que combinam com você</h2>
        <SeloIA />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sugestoes.cargos.map((cargo) => (
          <CardCargo key={cargo.cargo} cargo={cargo} />
        ))}
      </div>

      <p className="flex items-start gap-2 rounded-lg bg-slate-100 px-3 py-2.5 text-xs text-slate-600">
        <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-slate-400" aria-hidden="true" />
        Os links abrem a busca já pronta no próprio site. O Encaixe não coleta dados desses sites.
      </p>
      <p className="px-1 text-xs leading-relaxed text-slate-500">
        A IA pode errar: a aderência é uma estimativa. Geradas {tempoRelativo(sugestoes.atualizado_em)} ·
        modelo {sugestoes.modelo_ia} · prompt {sugestoes.versao_prompt}.
      </p>
    </>
  );
}

function Rotulo({ children }) {
  return (
    <p className="mt-4 mb-1.5 text-[11px] font-semibold tracking-wider text-violet-700 uppercase">
      {children}
    </p>
  );
}

function CardCargo({ cargo }) {
  return (
    <article className="flex flex-col rounded-xl border border-violet-100 bg-violet-50/50 p-5">
      <h3 className="font-semibold text-slate-900">{cargo.cargo}</h3>
      {cargo.area && <p className="mt-0.5 text-xs text-slate-500">{cargo.area}</p>}
      <div className="mt-2.5 flex items-center gap-2">
        <SeloNota nota={cargo.nota} />
        <span className="text-xs text-slate-500">aderência estimada</span>
      </div>

      <Rotulo>Por que combina</Rotulo>
      <p className="text-sm leading-relaxed text-slate-700">{cargo.por_que}</p>

      {cargo.palavras_chave.length > 0 && (
        <>
          <Rotulo>Palavras-chave</Rotulo>
          <ul className="flex flex-wrap gap-1.5">
            {cargo.palavras_chave.map((palavra) => (
              <li key={palavra} className="rounded-full bg-white px-2.5 py-1 text-xs text-slate-700 ring-1 ring-slate-200">
                {palavra}
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="mt-auto pt-1">
        <Rotulo>Buscar “{cargo.busca}”</Rotulo>
        <ul className="space-y-2">
          {cargo.links.map((link) => (
            <li key={link.site}>
              <a
                href={link.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-medium text-blue-600 transition hover:border-blue-300 hover:bg-blue-50"
              >
                Abrir busca no {link.site}
                <ExternalLink className="size-4 shrink-0" aria-hidden="true" />
                <span className="sr-only">(abre em nova aba)</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

function SemCurriculo() {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <Sparkles className="mx-auto size-8 text-violet-400" aria-hidden="true" />
      <h2 className="mt-3 font-semibold text-slate-900">Cadastre seu currículo primeiro</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
        A IA usa o seu currículo e as suas preferências para sugerir cargos e palavras-chave de busca.
      </p>
      <LinkBotao para="/curriculo" className="mt-5">
        Cadastrar currículo
      </LinkBotao>
    </div>
  );
}
