import { FileText, Sparkles, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { lerErros } from "../api";
import AvisoPrivacidade from "../components/AvisoPrivacidade";
import Cabecalho from "../components/Cabecalho";
import {
  AvisoErro,
  Botao,
  CampoAreaTexto,
  CampoTexto,
  OpcoesChip,
} from "../components/Formulario";
import { dataCurta } from "../vagas";

const STATUS_INICIAIS = [
  { valor: "interessado", rotulo: "Interessado" },
  { valor: "candidatado", rotulo: "Candidatado" },
];

const PASSOS_IA = [
  "Lê os requisitos e os diferenciais da vaga.",
  "Compara com o seu currículo.",
  "Mostra a nota de aderência, o que você já atende, as lacunas e sugestões de ajuste.",
];

// POST /api/vagas/ cria a vaga. "Analisar com IA" abre a tela da vaga já pedindo a análise.
export default function NovaVaga() {
  const navegar = useNavigate();
  const [vaga, setVaga] = useState({
    titulo: "",
    empresa: "",
    link: "",
    local: "",
    descricao: "",
    status: "interessado",
  });
  const [curriculo, setCurriculo] = useState(undefined); // undefined = carregando, null = não tem
  const [erros, setErros] = useState({ geral: "", campos: {} });
  const [enviando, setEnviando] = useState(null); // "salvar" | "analisar" | null

  useEffect(() => {
    api
      .get("/curriculo/")
      .then(({ data }) => setCurriculo(data))
      .catch((erro) => setCurriculo(erro.response?.status === 404 ? null : false));
  }, []);

  const semCurriculo = curriculo === null;

  function mudar(campo) {
    return (evento) => setVaga((atual) => ({ ...atual, [campo]: evento.target.value }));
  }

  async function aoEnviar(evento) {
    evento.preventDefault();
    // Qual dos dois botões enviou o formulário.
    const analisar = evento.nativeEvent.submitter?.value === "analisar" && !semCurriculo;
    setEnviando(analisar ? "analisar" : "salvar");
    setErros({ geral: "", campos: {} });
    try {
      const { data } = await api.post("/vagas/", vaga);
      if (analisar) {
        navegar(`/vagas/${data.id}`, { state: { analisar: true } });
      } else {
        navegar("/vagas");
      }
    } catch (erro) {
      setErros(lerErros(erro));
      setEnviando(null);
    }
  }

  return (
    <section>
      <Cabecalho
        voltar={{ para: "/vagas", rotulo: "Minhas vagas" }}
        titulo="Nova vaga"
        subtitulo="Cole a descrição da vaga. Você pode analisar agora ou salvar e analisar depois."
      />

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <form
          onSubmit={aoEnviar}
          className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6"
        >
          <AvisoErro>{erros.geral}</AvisoErro>
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto
              id="titulo"
              rotulo="Cargo"
              placeholder="Estágio em Dados"
              value={vaga.titulo}
              onChange={mudar("titulo")}
              erro={erros.campos.titulo}
              maxLength={200}
              required
            />
            <CampoTexto
              id="empresa"
              rotulo="Empresa"
              placeholder="Nuvem Pay"
              value={vaga.empresa}
              onChange={mudar("empresa")}
              erro={erros.campos.empresa}
              maxLength={200}
              required
            />
            <CampoTexto
              id="link"
              rotulo="Link da vaga (opcional)"
              type="url"
              placeholder="https://..."
              value={vaga.link}
              onChange={mudar("link")}
              erro={erros.campos.link}
              maxLength={500}
            />
            <CampoTexto
              id="local"
              rotulo="Local (opcional)"
              placeholder="São Paulo · Híbrido"
              value={vaga.local}
              onChange={mudar("local")}
              erro={erros.campos.local}
              maxLength={120}
            />
          </div>
          <CampoAreaTexto
            id="descricao"
            rotulo="Descrição da vaga"
            rows={12}
            placeholder={"O que você vai fazer...\n\nRequisitos...\n\nDiferenciais..."}
            value={vaga.descricao}
            onChange={mudar("descricao")}
            erro={erros.campos.descricao}
            dica="Cole o texto inteiro do anúncio: atividades, requisitos e diferenciais."
            required
          />
          <OpcoesChip
            nome="status"
            legenda="Salvar em"
            opcoes={STATUS_INICIAIS}
            valor={vaga.status}
            aoMudar={(status) => setVaga((atual) => ({ ...atual, status }))}
          />

          <div className="flex flex-col-reverse gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:justify-end">
            <Botao
              type="submit"
              value="salvar"
              variante="secundario"
              carregando={enviando === "salvar"}
              disabled={enviando !== null}
              textoCarregando="Salvando..."
            >
              Salvar sem analisar
            </Botao>
            <Botao
              type="submit"
              value="analisar"
              variante="ia"
              carregando={enviando === "analisar"}
              disabled={enviando !== null || semCurriculo}
              textoCarregando="Salvando..."
              title={semCurriculo ? "Cadastre seu currículo para analisar" : undefined}
            >
              <Sparkles className="size-4" aria-hidden="true" />
              Analisar com IA
            </Botao>
          </div>
        </form>

        <aside className="space-y-4">
          <div className="rounded-xl border border-violet-200 bg-violet-50/70 p-5">
            <h2 className="flex items-center gap-2 font-semibold text-slate-900">
              <Sparkles className="size-4 text-violet-600" aria-hidden="true" />O que a IA vai fazer
            </h2>
            <ol className="mt-4 space-y-3 text-sm text-slate-700">
              {PASSOS_IA.map((passo, indice) => (
                <li key={passo} className="flex gap-3">
                  <span className="grid size-5 shrink-0 place-items-center rounded-full bg-violet-600 text-[11px] font-semibold text-white">
                    {indice + 1}
                  </span>
                  {passo}
                </li>
              ))}
            </ol>
            <p className="mt-4 text-xs font-medium text-violet-700">Leva uns 10 a 20 segundos.</p>
            <AvisoPrivacidade curto className="mt-4 bg-white" />
          </div>

          <CartaoCurriculo curriculo={curriculo} />
        </aside>
      </div>
    </section>
  );
}

function CartaoCurriculo({ curriculo }) {
  if (curriculo === undefined || curriculo === false) return null;

  if (curriculo === null) {
    return (
      <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <p>
          Você ainda não cadastrou seu currículo. Dá para salvar a vaga, mas a análise precisa dele.{" "}
          <Link to="/curriculo" className="font-semibold underline">
            Cadastrar currículo
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4">
      <FileText className="size-5 shrink-0 text-blue-600" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-900">Currículo usado</p>
        <p className="text-xs text-slate-500">Atualizado em {dataCurta(curriculo.atualizado_em)}</p>
      </div>
      <Link to="/curriculo" className="text-sm font-medium text-blue-600 hover:underline">
        Ver
      </Link>
    </div>
  );
}
