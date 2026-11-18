import { CheckCircle2, FileText, TriangleAlert, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { lerErros, TEMPO_IA } from "../api";
import AvisoPrivacidade from "../components/AvisoPrivacidade";
import Cabecalho from "../components/Cabecalho";
import { AvisoErro, BotaoPrimario, CampoAreaTexto, CampoArquivo } from "../components/Formulario";
import TelaCarregando from "../components/TelaCarregando";

// Mesmo limite do backend (vagas/pdf.py): arquivo maior que isso nem sai do navegador.
const TAMANHO_MAX_PDF = 5 * 1024 * 1024;

// Passo 2 do onboarding: depois do cadastro o usuário cai aqui.
// Ele pode enviar o PDF do currículo (POST /api/curriculo/pdf/ devolve o texto para
// conferir, sem salvar nada) ou colar o texto na mão. O PUT /api/curriculo/ salva o
// texto e a IA devolve o currículo organizado em `dados`.
export default function Curriculo() {
  const [texto, setTexto] = useState("");
  const [dados, setDados] = useState(null);
  // Texto salvo que a IA ainda não organizou (ela falhou da última vez).
  const [pendente, setPendente] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  // PDF lido nesta visita: { nome, paginas, cortado }. Vira o aviso em cima do campo.
  const [pdf, setPdf] = useState(null);
  const [lendoPdf, setLendoPdf] = useState(false);
  const [erros, setErros] = useState({ geral: "", campos: {} });

  useEffect(() => {
    api
      .get("/curriculo/")
      .then(({ data }) => {
        setTexto(data.texto);
        setDados(data.desatualizado ? null : data.dados);
        setPendente(data.desatualizado);
      })
      .catch((erro) => {
        if (erro.response?.status !== 404) setErros(lerErros(erro));
      })
      .finally(() => setCarregando(false));
  }, []);

  /** Manda o PDF para o backend e põe o texto extraído no campo, para o usuário conferir. */
  async function lerPdf(arquivo) {
    setPdf(null);
    if (!arquivo.name.toLowerCase().endsWith(".pdf")) {
      setErros({ geral: "Por enquanto só dá para enviar o currículo em PDF.", campos: {} });
      return;
    }
    if (arquivo.size > TAMANHO_MAX_PDF) {
      setErros({
        geral: "O arquivo passou de 5 MB. Exporte o PDF de novo ou cole o texto no campo.",
        campos: {},
      });
      return;
    }

    setLendoPdf(true);
    setErros({ geral: "", campos: {} });
    try {
      const corpo = new FormData();
      corpo.append("arquivo", arquivo);
      const { data } = await api.post("/curriculo/pdf/", corpo);
      setTexto(data.texto);
      setPdf({ nome: arquivo.name, paginas: data.paginas, cortado: data.cortado });
    } catch (erro) {
      setErros(lerErros(erro));
    } finally {
      setLendoPdf(false);
    }
  }

  async function aoEnviar(evento) {
    evento.preventDefault();
    setSalvando(true);
    setErros({ geral: "", campos: {} });
    try {
      const { data } = await api.put("/curriculo/", { texto }, { timeout: TEMPO_IA });
      setDados(data.dados);
      setPendente(false);
      setPdf(null);
    } catch (erro) {
      setDados(null);
      // 502: o texto foi salvo, só a IA falhou. Clicar em Salvar de novo tenta outra vez.
      setPendente(erro.response?.status === 502);
      setErros(lerErros(erro));
    } finally {
      setSalvando(false);
    }
  }

  if (carregando) return <TelaCarregando dentroDoLayout />;

  return (
    <section className="max-w-3xl">
      <Cabecalho
        titulo="Seu currículo"
        subtitulo="Envie o PDF do seu currículo ou cole o texto. A IA organiza as informações e usa esse resumo para analisar cada vaga e escrever as cartas."
      />

      <form
        onSubmit={aoEnviar}
        className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6"
      >
        <AvisoErro>{erros.geral}</AvisoErro>
        {pendente && !erros.geral && (
          <p className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-800">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            Seu currículo está salvo, mas a IA ainda não conseguiu organizá-lo. Clique em Salvar
            currículo para tentar de novo.
          </p>
        )}

        <EnvioPdf lendo={lendoPdf} desabilitado={salvando} aoEscolher={lerPdf} />
        {pdf && <AvisoPdf pdf={pdf} />}

        <CampoAreaTexto
          id="texto"
          rotulo="Texto do currículo"
          rows={14}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Formação, experiências, projetos, habilidades, idiomas..."
          erro={erros.campos.texto}
          required
        />
        <AvisoPrivacidade />
        <BotaoPrimario type="submit" carregando={salvando} textoCarregando="Organizando com a IA...">
          Salvar currículo
        </BotaoPrimario>
      </form>

      {dados && <ResumoCurriculo dados={dados} />}
    </section>
  );
}

/** Caixa de envio do PDF: botão para escolher o arquivo e área que aceita arrastar e soltar. */
function EnvioPdf({ lendo, desabilitado, aoEscolher }) {
  const [arrastando, setArrastando] = useState(false);
  const bloqueado = lendo || desabilitado;

  function aoSoltar(evento) {
    evento.preventDefault();
    setArrastando(false);
    const arquivo = evento.dataTransfer.files?.[0];
    if (arquivo && !bloqueado) aoEscolher(arquivo);
  }

  return (
    <div
      onDragOver={(evento) => {
        evento.preventDefault();
        if (!bloqueado) setArrastando(true);
      }}
      onDragLeave={() => setArrastando(false)}
      onDrop={aoSoltar}
      className={`flex flex-wrap items-center justify-between gap-x-4 gap-y-3 rounded-lg border border-dashed px-3 py-3 transition ${
        arrastando ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-slate-50"
      }`}
    >
      <p className="flex max-w-md items-start gap-2.5 text-sm text-slate-600">
        <Upload className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
        <span>
          Tem o currículo em PDF? <span className="hidden sm:inline">Arraste aqui ou </span>
          envie o arquivo que a gente lê o texto para você. Até 5 MB, e o PDF precisa ter texto (não
          funciona com currículo escaneado).
        </span>
      </p>
      <CampoArquivo
        id="pdf"
        accept="application/pdf,.pdf"
        aoEscolher={aoEscolher}
        carregando={lendo}
        textoCarregando="Lendo o PDF..."
        disabled={desabilitado}
      >
        <Upload className="size-4" aria-hidden="true" />
        Escolher PDF
      </CampoArquivo>
    </div>
  );
}

/** Confirmação verde depois de ler o PDF, pedindo para o usuário conferir o texto. */
function AvisoPdf({ pdf }) {
  const paginas = pdf.paginas === 1 ? "1 página" : `${pdf.paginas} páginas`;
  return (
    <p className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-sm text-emerald-800">
      <FileText className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>
        Texto lido de <span className="font-medium">{pdf.nome}</span> ({paginas}). Confira abaixo,
        arrume o que a extração bagunçou e clique em Salvar currículo.
        {pdf.cortado && " O arquivo é longo, então lemos só o começo."}
      </span>
    </p>
  );
}

function ResumoCurriculo({ dados }) {
  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
      <div className="flex items-center gap-2 text-sm font-medium text-emerald-700">
        <CheckCircle2 className="size-4" aria-hidden="true" />
        Currículo organizado pela IA. Confira se está tudo certo.
      </div>
      {dados.resumo && <p className="mt-3 text-sm text-slate-700">{dados.resumo}</p>}

      <Lista titulo="Formação" itens={dados.formacao?.map((f) => juntar(f.curso, f.instituicao, f.periodo))} />
      <Lista
        titulo="Experiências"
        itens={dados.experiencias?.map((e) => juntar(e.cargo, e.empresa, e.periodo))}
      />
      <Lista titulo="Projetos" itens={dados.projetos} />
      <Etiquetas titulo="Habilidades" itens={dados.habilidades} />
      <Etiquetas titulo="Idiomas" itens={dados.idiomas} />

      <Link
        to="/preferencias"
        className="mt-6 inline-block text-sm font-medium text-blue-600 hover:underline"
      >
        Próximo passo: suas preferências →
      </Link>
    </div>
  );
}

const juntar = (...partes) => partes.filter(Boolean).join(" · ");

function Lista({ titulo, itens }) {
  if (!itens?.length) return null;
  return (
    <div className="mt-5">
      <h2 className="text-sm font-semibold text-slate-900">{titulo}</h2>
      <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {itens.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function Etiquetas({ titulo, itens }) {
  if (!itens?.length) return null;
  return (
    <div className="mt-5">
      <h2 className="text-sm font-semibold text-slate-900">{titulo}</h2>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {itens.map((item) => (
          <span key={item} className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
