import { CircleCheck, Sparkles } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { lerErros } from "../api";
import Cabecalho from "../components/Cabecalho";
import EscolhaMultipla from "../components/EscolhaMultipla";
import { AvisoErro, Botao, CampoTexto, LinkBotao } from "../components/Formulario";
import PassosOnboarding from "../components/PassosOnboarding";
import TelaCarregando from "../components/TelaCarregando";
import { AREAS_SUGERIDAS, MODALIDADES, STACK_SUGERIDA, TIPOS } from "../preferencias";

// GET /api/preferencias/ carrega; PUT salva. Quem nunca salvou (atualizado_em null) vê o
// passo 3 do onboarding: "Pular por agora" ou "Salvar e ver minhas vagas".
export default function Preferencias() {
  const navegar = useNavigate();
  const [preferencias, setPreferencias] = useState(null);
  const [onboarding, setOnboarding] = useState(false);
  const [erroCarregar, setErroCarregar] = useState("");
  const [erros, setErros] = useState({ geral: "", campos: {} });
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);

  const buscar = useCallback(() => {
    let ativo = true;
    api
      .get("/preferencias/")
      .then(({ data }) => {
        if (!ativo) return;
        setPreferencias(data);
        setOnboarding(data.atualizado_em === null);
      })
      .catch((erro) => ativo && setErroCarregar(lerErros(erro).geral));
    return () => {
      ativo = false;
    };
  }, []);

  useEffect(() => buscar(), [buscar]);

  function mudar(campo) {
    return (valor) => {
      setPreferencias((atual) => ({ ...atual, [campo]: valor }));
      setSalvo(false);
    };
  }

  async function aoEnviar(evento) {
    evento.preventDefault();
    setSalvando(true);
    setSalvo(false);
    setErros({ geral: "", campos: {} });
    const { areas, tipos, modalidades, cidade, stack, evitar } = preferencias;
    try {
      const { data } = await api.put("/preferencias/", { areas, tipos, modalidades, cidade, stack, evitar });
      if (onboarding) {
        navegar("/vagas");
        return;
      }
      setPreferencias(data);
      setSalvo(true);
    } catch (erro) {
      setErros(lerErros(erro));
    }
    setSalvando(false);
  }

  if (erroCarregar) {
    return (
      <section>
        <Cabecalho titulo="Suas preferências" />
        <AvisoErro
          aoTentarDeNovo={() => {
            setErroCarregar("");
            buscar();
          }}
        >
          {erroCarregar}
        </AvisoErro>
      </section>
    );
  }
  if (!preferencias) return <TelaCarregando dentroDoLayout />;

  return (
    <section className="max-w-5xl">
      {onboarding && (
        <div className="mb-4">
          <PassosOnboarding atual={2} />
        </div>
      )}
      <Cabecalho
        titulo="Suas preferências"
        subtitulo="Usamos isso para personalizar a análise, filtrar o kanban e sugerir buscas. Dá para mudar depois."
      />

      <form
        id="form-preferencias"
        onSubmit={aoEnviar}
        className="space-y-6 rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6"
      >
        <AvisoErro>{erros.geral}</AvisoErro>
        <div className="grid gap-x-10 gap-y-6 lg:grid-cols-2">
          <div className="space-y-6">
            <EscolhaMultipla
              id="areas"
              legenda="Áreas de interesse"
              opcoes={AREAS_SUGERIDAS}
              valores={preferencias.areas}
              aoMudar={mudar("areas")}
              permitirOutro
              placeholderOutro="Outra área"
              limite={10}
              erro={erros.campos.areas}
            />
            <EscolhaMultipla
              id="tipos"
              legenda="Tipo de vaga"
              opcoes={TIPOS}
              valores={preferencias.tipos}
              aoMudar={mudar("tipos")}
              erro={erros.campos.tipos}
            />
            <EscolhaMultipla
              id="modalidades"
              legenda="Modalidade"
              opcoes={MODALIDADES}
              valores={preferencias.modalidades}
              aoMudar={mudar("modalidades")}
              erro={erros.campos.modalidades}
            />
          </div>

          <div className="space-y-6">
            <CampoTexto
              id="cidade"
              rotulo="Cidade"
              placeholder="São Paulo, SP"
              autoComplete="address-level2"
              maxLength={120}
              value={preferencias.cidade}
              onChange={(e) => mudar("cidade")(e.target.value)}
              erro={erros.campos.cidade}
              dica="Usada no filtro do kanban e nos links de busca."
            />
            <EscolhaMultipla
              id="stack"
              legenda="Stack que quero usar"
              opcoes={STACK_SUGERIDA}
              valores={preferencias.stack}
              aoMudar={mudar("stack")}
              permitirOutro
              placeholderOutro="Outra"
              limite={15}
              erro={erros.campos.stack}
            />
            <CampoTexto
              id="evitar"
              rotulo="Prefiro evitar"
              placeholder="Vagas com mais de 30 horas semanais"
              maxLength={300}
              value={preferencias.evitar}
              onChange={(e) => mudar("evitar")(e.target.value)}
              erro={erros.campos.evitar}
            />
          </div>
        </div>

        <p className="flex items-start gap-2 rounded-lg bg-blue-50 px-3 py-2.5 text-xs leading-relaxed text-blue-800">
          <Sparkles className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          Exemplo: se a vaga exige 40 horas semanais e você escreveu isso em “Prefiro evitar”, a
          análise avisa antes de você se candidatar.
        </p>
      </form>

      <div className="mt-5 flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center sm:justify-end">
        {onboarding ? (
          <>
            <Link
              to="/vagas"
              className="py-2 text-center text-sm font-medium text-blue-600 hover:underline sm:px-3"
            >
              Pular por agora
            </Link>
            <Botao type="submit" form="form-preferencias" carregando={salvando} textoCarregando="Salvando...">
              Salvar e ver minhas vagas
            </Botao>
          </>
        ) : (
          <>
            {salvo && (
              <p role="status" className="flex items-center gap-1.5 text-sm text-emerald-700 sm:mr-auto">
                <CircleCheck className="size-4" aria-hidden="true" />
                Preferências salvas.
                <Link to="/sugestoes" className="font-medium text-blue-600 hover:underline">
                  Ver sugestões de busca
                </Link>
              </p>
            )}
            <LinkBotao para="/vagas" variante="secundario">
              Voltar às vagas
            </LinkBotao>
            <Botao type="submit" form="form-preferencias" carregando={salvando} textoCarregando="Salvando...">
              Salvar preferências
            </Botao>
          </>
        )}
      </div>
    </section>
  );
}
