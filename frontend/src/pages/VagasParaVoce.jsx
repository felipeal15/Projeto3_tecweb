import { Check, ExternalLink, MapPin, Plus, Search, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { lerErros, TEMPO_IA } from "../api";
import Cabecalho from "../components/Cabecalho";
import CarregandoIA from "../components/CarregandoIA";
import { AvisoErro, Botao } from "../components/Formulario";
import { SeloIA, SeloNota } from "../components/Selos";
import { tempoRelativo } from "../vagas";

// GET /api/vagas-reais/?q= busca vagas reais (Adzuna) e a IA ranqueia pelo currículo.
// Sem `q`, o backend usa a melhor sugestão de busca ou a primeira área das preferências.
export default function VagasParaVoce() {
  const [termo, setTermo] = useState("");
  const [resultado, setResultado] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  // Quem chama liga o `carregando` (no primeiro render ele já começa ligado).
  const buscar = useCallback(
    (q = "") =>
      api
        .get("/vagas-reais/", { params: q ? { q } : {}, timeout: TEMPO_IA })
        .then(({ data }) => {
          setResultado(data);
          setTermo(data.termo);
        })
        .catch((e) => setErro(lerErros(e).geral))
        .finally(() => setCarregando(false)),
    [],
  );

  useEffect(() => {
    buscar();
  }, [buscar]);

  function novaBusca() {
    setCarregando(true);
    setErro("");
    buscar(termo.trim());
  }

  function enviar(evento) {
    evento.preventDefault();
    if (termo.trim()) novaBusca();
  }

  function marcarSalva(id, vagaId) {
    setResultado((atual) => ({
      ...atual,
      vagas: atual.vagas.map((v) => (v.id === id ? { ...v, salva_id: vagaId } : v)),
    }));
  }

  return (
    <section>
      <Cabecalho
        titulo="Vagas para você"
        subtitulo="Vagas reais publicadas nos últimos 30 dias, ordenadas pela aderência ao seu currículo."
      />

      <form onSubmit={enviar} className="flex flex-wrap gap-2" role="search">
        <label htmlFor="termo" className="sr-only">
          O que você procura
        </label>
        <input
          id="termo"
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          maxLength={80}
          placeholder="ex.: estágio dados"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm shadow-xs outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-600/20"
        />
        <Botao type="submit" carregando={carregando} textoCarregando="Buscando...">
          <Search className="size-4" aria-hidden="true" />
          Buscar
        </Botao>
      </form>
      {resultado?.cidade && (
        <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
          <MapPin className="size-3.5" aria-hidden="true" />
          Em {resultado.cidade}, pela cidade das suas{" "}
          <Link to="/preferencias" className="font-medium text-blue-600 hover:underline">
            preferências
          </Link>
          .
        </p>
      )}

      <div className="mt-6 space-y-4">
        {carregando ? (
          <CarregandoIA
            titulo="Buscando vagas e ranqueando com a IA"
            descricao="Buscamos vagas reais no Adzuna e a IA compara cada uma com o seu currículo."
          />
        ) : erro ? (
          <AvisoErro aoTentarDeNovo={novaBusca}>{erro}</AvisoErro>
        ) : (
          resultado && <Lista resultado={resultado} aoSalvar={marcarSalva} />
        )}
      </div>
    </section>
  );
}

function Lista({ resultado, aoSalvar }) {
  const { vagas, ranqueada, erro_ranking: erroRanking } = resultado;

  if (vagas.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center text-sm text-slate-500">
        Nenhuma vaga recente para “{resultado.termo}”. Tente palavras mais gerais.
      </div>
    );
  }

  return (
    <>
      {erroRanking ? (
        <p className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <TriangleAlert className="size-4 shrink-0" aria-hidden="true" />
          A IA não conseguiu ranquear agora ({erroRanking}). As vagas aparecem sem nota.
        </p>
      ) : (
        !ranqueada && (
          <p className="rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-600">
            <Link to="/curriculo" className="font-medium text-blue-600 hover:underline">
              Cadastre seu currículo
            </Link>{" "}
            para a IA ordenar as vagas pela aderência.
          </p>
        )
      )}

      <ul className="space-y-3">
        {vagas.map((vaga) => (
          <li key={vaga.id}>
            <CardVaga vaga={vaga} aoSalvar={aoSalvar} />
          </li>
        ))}
      </ul>

      <p className="px-1 text-xs leading-relaxed text-slate-500">
        Vagas por{" "}
        <a href="https://www.adzuna.com.br" target="_blank" rel="noreferrer" className="font-semibold text-blue-600 hover:underline">
          Adzuna
        </a>
        . A descrição é só um trecho: antes de analisar, abra o anúncio e cole a descrição completa na vaga.
        {ranqueada && ` A nota é uma estimativa da IA · modelo ${resultado.modelo_ia} · prompt ${resultado.versao_prompt}.`}
      </p>
    </>
  );
}

function CardVaga({ vaga, aoSalvar }) {
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  async function salvar() {
    setSalvando(true);
    setErro("");
    try {
      const { titulo, empresa, local, descricao, link } = vaga;
      const { data } = await api.post("/vagas/", { titulo, empresa, local, descricao, link });
      aoSalvar(vaga.id, data.id);
    } catch (e) {
      setErro(lerErros(e).geral || "Não foi possível salvar a vaga.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-slate-900">{vaga.titulo}</h3>
          <p className="mt-0.5 text-sm text-slate-500">
            {vaga.empresa}
            {vaga.local && ` · ${vaga.local}`}
            {vaga.criado_em && ` · ${tempoRelativo(vaga.criado_em)}`}
          </p>
        </div>
        {vaga.nota !== null && <SeloNota nota={vaga.nota} />}
      </div>

      {vaga.motivo && (
        <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-slate-700">
          <SeloIA />
          {vaga.motivo}
        </p>
      )}

      {vaga.fora_das_preferencias.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Fora das suas preferências">
          {vaga.fora_das_preferencias.map((item) => (
            <li key={item} className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800 ring-1 ring-amber-200">
              {item}
            </li>
          ))}
        </ul>
      )}

      <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-slate-600">{vaga.descricao}</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {vaga.salva_id ? (
          <Link
            to={`/vagas/${vaga.salva_id}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-100"
          >
            <Check className="size-4" aria-hidden="true" />
            No kanban · abrir
          </Link>
        ) : (
          <Botao onClick={salvar} carregando={salvando} textoCarregando="Salvando..." className="py-2">
            <Plus className="size-4" aria-hidden="true" />
            Salvar no kanban
          </Botao>
        )}
        {vaga.link && (
          <a
            href={vaga.link}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Ver anúncio
            <ExternalLink className="size-4" aria-hidden="true" />
            <span className="sr-only">(abre em nova aba)</span>
          </a>
        )}
        {erro && <span className="text-sm text-red-600">{erro}</span>}
      </div>
    </article>
  );
}
