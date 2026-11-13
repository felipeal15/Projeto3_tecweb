import { CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { lerErros } from "../api";
import { AvisoErro, BotaoPrimario } from "../components/Formulario";
import TelaCarregando from "../components/TelaCarregando";

// Passo 2 do onboarding: depois do cadastro o usuário cai aqui.
// PUT /api/curriculo/ salva o texto e a IA devolve o currículo organizado em `dados`.
export default function Curriculo() {
  const [texto, setTexto] = useState("");
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erros, setErros] = useState({ geral: "", campos: {} });

  useEffect(() => {
    api
      .get("/curriculo/")
      .then(({ data }) => {
        setTexto(data.texto);
        setDados(data.desatualizado ? null : data.dados);
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
      const { data } = await api.put("/curriculo/", { texto });
      setDados(data.dados);
    } catch (erro) {
      setDados(null);
      setErros(lerErros(erro));
    } finally {
      setSalvando(false);
    }
  }

  if (carregando) return <TelaCarregando />;

  return (
    <section className="max-w-3xl">
      <h1 className="text-2xl font-bold text-slate-900">Seu currículo</h1>
      <p className="mt-1 text-sm text-slate-500">
        Cole o texto do seu currículo. A IA organiza as informações e usa esse resumo para analisar
        cada vaga. O texto é enviado para a API do Google Gemini.
      </p>

      <form onSubmit={aoEnviar} className="mt-6 space-y-4">
        <AvisoErro>{erros.geral}</AvisoErro>
        <div>
          <label htmlFor="texto" className="mb-1.5 block text-sm font-medium text-slate-700">
            Texto do currículo
          </label>
          <textarea
            id="texto"
            rows={14}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Formação, experiências, projetos, habilidades, idiomas..."
            aria-invalid={erros.campos.texto ? true : undefined}
            aria-describedby={erros.campos.texto ? "texto-ajuda" : undefined}
            className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-900 shadow-xs outline-none transition placeholder:text-slate-400 focus:ring-2 focus:ring-blue-600/20 ${
              erros.campos.texto ? "border-red-400 focus:border-red-500" : "border-slate-300 focus:border-blue-600"
            }`}
            required
          />
          {erros.campos.texto && (
            <p id="texto-ajuda" className="mt-1.5 text-xs text-red-600">
              {erros.campos.texto}
            </p>
          )}
        </div>
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
    <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6">
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
