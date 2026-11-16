import { CheckCircle2, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { lerErros, TEMPO_IA } from "../api";
import AvisoPrivacidade from "../components/AvisoPrivacidade";
import Cabecalho from "../components/Cabecalho";
import { AvisoErro, BotaoPrimario, CampoAreaTexto } from "../components/Formulario";
import TelaCarregando from "../components/TelaCarregando";

// Passo 2 do onboarding: depois do cadastro o usuário cai aqui.
// PUT /api/curriculo/ salva o texto e a IA devolve o currículo organizado em `dados`.
export default function Curriculo() {
  const [texto, setTexto] = useState("");
  const [dados, setDados] = useState(null);
  // Texto salvo que a IA ainda não organizou (ela falhou da última vez).
  const [pendente, setPendente] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
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

  async function aoEnviar(evento) {
    evento.preventDefault();
    setSalvando(true);
    setErros({ geral: "", campos: {} });
    try {
      const { data } = await api.put("/curriculo/", { texto }, { timeout: TEMPO_IA });
      setDados(data.dados);
      setPendente(false);
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
        subtitulo="Cole o texto do seu currículo. A IA organiza as informações e usa esse resumo para analisar cada vaga e escrever as cartas."
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
        to="/nova-vaga"
        className="mt-6 inline-block text-sm font-medium text-blue-600 hover:underline"
      >
        Próximo passo: analisar uma vaga →
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
