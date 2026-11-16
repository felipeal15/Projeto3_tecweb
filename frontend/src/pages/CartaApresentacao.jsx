import { Check, CircleCheck, Copy, PenLine, RefreshCw, Sparkles, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { lerErros, TEMPO_IA } from "../api";
import AvisoPrivacidade from "../components/AvisoPrivacidade";
import Cabecalho from "../components/Cabecalho";
import CarregandoIA from "../components/CarregandoIA";
import { AvisoErro, Botao, CampoAreaTexto, LinkBotao, OpcoesChip } from "../components/Formulario";
import { SeloIA } from "../components/Selos";
import TelaCarregando from "../components/TelaCarregando";

const TONS = [
  { valor: "formal", rotulo: "Formal" },
  { valor: "neutro", rotulo: "Neutro" },
  { valor: "entusiasmado", rotulo: "Entusiasmado" },
];
const TAMANHOS = [
  { valor: "curta", rotulo: "Curta" },
  { valor: "media", rotulo: "Média" },
];

// Rota /vagas/:id/carta. GET /api/vagas/<id>/carta/ traz a carta salva,
// POST { tom, tamanho } pede uma versão nova à IA e PATCH { texto } salva a edição.
export default function CartaApresentacao() {
  const { id } = useParams();
  const [vaga, setVaga] = useState(null);
  const [carta, setCarta] = useState(null); // como está salva no backend
  const [texto, setTexto] = useState(""); // como está na caixa de texto
  const [tom, setTom] = useState("neutro");
  const [tamanho, setTamanho] = useState("curta");
  const [temCurriculo, setTemCurriculo] = useState(null);
  const [erroCarregar, setErroCarregar] = useState("");
  const [gerando, setGerando] = useState(false);
  const [erroIA, setErroIA] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erroSalvar, setErroSalvar] = useState("");
  const [aviso, setAviso] = useState(""); // "Carta salva." / "Copiada!"

  const alterado = carta !== null && texto !== carta.texto;

  const usarCarta = useCallback((dados) => {
    setCarta(dados);
    setTexto(dados?.texto ?? "");
    if (dados) {
      setTom(dados.tom);
      setTamanho(dados.tamanho);
    }
  }, []);

  // Busca a vaga, a carta e se existe currículo. Devolve a função que ignora a resposta.
  const buscar = useCallback(() => {
    let ativo = true;
    const seNaoExiste = (valor) => (erro) =>
      erro.response?.status === 404 ? valor : Promise.reject(erro);

    Promise.all([
      api.get(`/vagas/${id}/`),
      api.get(`/vagas/${id}/carta/`).catch(seNaoExiste({ data: null })),
      api
        .get("/curriculo/")
        .then(() => true)
        .catch(seNaoExiste(false)),
    ])
      .then(([respostaVaga, respostaCarta, curriculo]) => {
        if (!ativo) return;
        setVaga(respostaVaga.data);
        usarCarta(respostaCarta.data);
        setTemCurriculo(curriculo);
      })
      .catch((erro) => {
        if (!ativo) return;
        setErroCarregar(
          erro.response?.status === 404 ? "Vaga não encontrada." : lerErros(erro).geral,
        );
      });

    return () => {
      ativo = false;
    };
  }, [id, usarCarta]);

  useEffect(() => buscar(), [buscar]);

  function tentarDeNovo() {
    setErroCarregar("");
    buscar();
  }

  // Avisa antes de fechar a aba com edição não salva.
  useEffect(() => {
    if (!alterado) return;
    const avisar = (evento) => {
      evento.preventDefault();
      evento.returnValue = "";
    };
    window.addEventListener("beforeunload", avisar);
    return () => window.removeEventListener("beforeunload", avisar);
  }, [alterado]);

  // Some com "Carta salva." / "Copiada!" depois de alguns segundos.
  useEffect(() => {
    if (!aviso) return;
    const relogio = setTimeout(() => setAviso(""), 2500);
    return () => clearTimeout(relogio);
  }, [aviso]);

  async function gerar() {
    if (
      carta &&
      (alterado || carta.editada) &&
      !window.confirm("A nova versão substitui o texto atual, inclusive as suas edições. Continuar?")
    ) {
      return;
    }
    setGerando(true);
    setErroIA("");
    setErroSalvar("");
    try {
      const { data } = await api.post(`/vagas/${id}/carta/`, { tom, tamanho }, { timeout: TEMPO_IA });
      usarCarta(data);
    } catch (erro) {
      setErroIA(lerErros(erro).geral);
    } finally {
      setGerando(false);
    }
  }

  async function salvar() {
    setSalvando(true);
    setErroSalvar("");
    try {
      const { data } = await api.patch(`/vagas/${id}/carta/`, { texto });
      usarCarta(data);
      setAviso("Carta salva.");
    } catch (erro) {
      const { geral, campos } = lerErros(erro);
      setErroSalvar(campos.texto || geral);
    } finally {
      setSalvando(false);
    }
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(texto);
      setAviso("Copiada!");
    } catch {
      setErroSalvar("Não foi possível copiar. Selecione o texto e use Ctrl+C.");
    }
  }

  if (erroCarregar) {
    return (
      <section>
        <Cabecalho voltar={{ para: `/vagas/${id}`, rotulo: "Análise da vaga" }} titulo="Carta de apresentação" />
        <AvisoErro aoTentarDeNovo={erroCarregar === "Vaga não encontrada." ? undefined : tentarDeNovo}>
          {erroCarregar}
        </AvisoErro>
      </section>
    );
  }

  if (!vaga) return <TelaCarregando dentroDoLayout />;

  const palavras = texto.trim() ? texto.trim().split(/\s+/).length : 0;

  return (
    <section>
      <Cabecalho
        voltar={{ para: `/vagas/${id}`, rotulo: "Análise da vaga" }}
        titulo="Carta de apresentação"
        subtitulo={`${vaga.titulo} · ${vaga.empresa}`}
      >
        {aviso && (
          <span role="status" className="flex items-center gap-1 text-sm font-medium text-emerald-700">
            <Check className="size-4" aria-hidden="true" />
            {aviso}
          </span>
        )}
        {carta && (
          <>
            <Botao variante="secundario" onClick={copiar} disabled={gerando || !texto.trim()}>
              <Copy className="size-4" aria-hidden="true" />
              Copiar
            </Botao>
            <Botao
              onClick={salvar}
              carregando={salvando}
              textoCarregando="Salvando..."
              disabled={!alterado || gerando}
            >
              Salvar carta
            </Botao>
          </>
        )}
      </Cabecalho>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold text-slate-900">Rascunho</h2>
            <div className="flex flex-wrap gap-1.5">
              {carta && <SeloIA />}
              {carta?.editada && (
                <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700">
                  <PenLine className="size-3" aria-hidden="true" />
                  Editada por você
                </span>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-3">
            <OpcoesChip nome="tom" legenda="Tom" opcoes={TONS} valor={tom} aoMudar={setTom} desabilitado={gerando} />
            <OpcoesChip
              nome="tamanho"
              legenda="Tamanho"
              opcoes={TAMANHOS}
              valor={tamanho}
              aoMudar={setTamanho}
              desabilitado={gerando}
            />
          </div>

          {carta?.desatualizada && !gerando && (
            <p className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-800">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              Seu currículo ou a vaga mudou depois desta carta. Gere outra versão para usar as
              informações novas.
            </p>
          )}
          {erroIA && !gerando && <AvisoErro aoTentarDeNovo={gerar}>{erroIA}</AvisoErro>}
          <AvisoErro>{erroSalvar}</AvisoErro>

          {gerando ? (
            <CarregandoIA
              titulo="Escrevendo a carta com a IA"
              descricao="A IA usa só os fatos do seu currículo que combinam com a vaga."
            />
          ) : carta ? (
            <>
              <CampoAreaTexto
                id="carta"
                aria-label="Texto da carta"
                rows={18}
                value={texto}
                onChange={(evento) => setTexto(evento.target.value)}
                maxLength={6000}
              />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="flex items-center gap-1.5 text-xs text-slate-500">
                  <PenLine className="size-3.5 shrink-0" aria-hidden="true" />
                  {alterado
                    ? "Alterações não salvas. Clique em Salvar carta."
                    : "Edite o texto à vontade e clique em Salvar carta."}
                  <span className="text-slate-400">· {palavras} palavras</span>
                </p>
                <Botao variante="ia" onClick={gerar}>
                  <RefreshCw className="size-4" aria-hidden="true" />
                  Gerar outra versão
                </Botao>
              </div>
            </>
          ) : (
            <SemCarta temCurriculo={temCurriculo} aoGerar={gerar} />
          )}
        </div>

        <aside className="space-y-4">
          {carta && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
              <h2 className="font-semibold text-slate-900">Fatos usados do seu currículo</h2>
              <ul className="mt-3 space-y-2">
                {carta.fatos_usados.map((fato, indice) => (
                  <li key={indice} className="flex gap-2 text-sm leading-relaxed text-slate-700">
                    <CircleCheck className="mt-0.5 size-4 shrink-0 text-emerald-600" aria-hidden="true" />
                    {fato}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-slate-500">
                Cada frase da carta deve se apoiar num destes fatos. Se aparecer algo que não está
                no seu <Link to="/curriculo" className="underline">currículo</Link>, apague.
              </p>
            </div>
          )}
          <p className="flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs leading-relaxed text-amber-800">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            A IA é instruída a não inventar experiência, mas pode errar. Revise antes de enviar.
          </p>
          <AvisoPrivacidade curto />
        </aside>
      </div>
    </section>
  );
}

function SemCarta({ temCurriculo, aoGerar }) {
  if (temCurriculo === false) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center">
        <p className="text-sm text-slate-600">
          A carta usa os fatos do seu currículo. Cadastre ele primeiro.
        </p>
        <LinkBotao para="/curriculo" className="mt-4">
          Cadastrar currículo
        </LinkBotao>
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center">
      <Sparkles className="mx-auto size-7 text-violet-400" aria-hidden="true" />
      <p className="mx-auto mt-3 max-w-sm text-sm text-slate-600">
        Escolha o tom e o tamanho, e a IA escreve um rascunho usando só o que está no seu currículo.
        Depois você edita como quiser.
      </p>
      <Botao variante="ia" onClick={aoGerar} className="mt-5">
        <Sparkles className="size-4" aria-hidden="true" />
        Gerar carta
      </Botao>
    </div>
  );
}
