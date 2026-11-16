import { CircleCheck, LoaderCircle, RotateCw } from "lucide-react";
import { Link } from "react-router-dom";

// Peças de formulário no estilo do fluxo de telas. Reaproveite nas outras telas.

function classeCampo(erro) {
  return `block w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-900 shadow-xs outline-none transition placeholder:text-slate-400 focus:ring-2 focus:ring-blue-600/20 disabled:bg-slate-50 disabled:text-slate-500 ${
    erro ? "border-red-400 focus:border-red-500" : "border-slate-300 focus:border-blue-600"
  }`;
}

function Ajuda({ id, erro, dica }) {
  if (!erro && !dica) return null;
  return (
    <p id={id} className={`mt-1.5 text-xs ${erro ? "text-red-600" : "text-slate-500"}`}>
      {erro || dica}
    </p>
  );
}

/** Campo com rótulo, dica e mensagem de erro. Aceita as props normais de <input>. */
export function CampoTexto({ id, rotulo, erro, dica, ...props }) {
  const idAjuda = `${id}-ajuda`;
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {rotulo}
      </label>
      <input
        id={id}
        name={id}
        aria-invalid={erro ? true : undefined}
        aria-describedby={erro || dica ? idAjuda : undefined}
        className={classeCampo(erro)}
        {...props}
      />
      <Ajuda id={idAjuda} erro={erro} dica={dica} />
    </div>
  );
}

/** Igual ao CampoTexto, mas com <textarea> (currículo, descrição da vaga, carta). */
export function CampoAreaTexto({ id, rotulo, erro, dica, className = "", ...props }) {
  const idAjuda = `${id}-ajuda`;
  return (
    <div>
      {rotulo && (
        <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
          {rotulo}
        </label>
      )}
      <textarea
        id={id}
        name={id}
        aria-invalid={erro ? true : undefined}
        aria-describedby={erro || dica ? idAjuda : undefined}
        className={`${classeCampo(erro)} leading-relaxed ${className}`}
        {...props}
      />
      <Ajuda id={idAjuda} erro={erro} dica={dica} />
    </div>
  );
}

const BASE_BOTAO =
  "inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold whitespace-nowrap shadow-xs transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60";

// azul: ação principal · ia: ações que chamam a IA (roxo, como no fluxo de telas) · secundario: branco
const VARIANTES = {
  azul: "bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-blue-600",
  ia: "bg-violet-600 text-white hover:bg-violet-700 focus-visible:outline-violet-600",
  secundario:
    "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 focus-visible:outline-blue-600",
};

/**
 * Botão com variantes. Com `carregando`, fica desabilitado, gira um ícone
 * e mostra `textoCarregando`.
 */
export function Botao({
  variante = "azul",
  carregando = false,
  textoCarregando,
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      disabled={carregando || disabled}
      aria-busy={carregando || undefined}
      className={`${BASE_BOTAO} ${VARIANTES[variante]} ${className}`}
      {...props}
    >
      {carregando ? (
        <>
          <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
          {textoCarregando ?? children}
        </>
      ) : (
        children
      )}
    </button>
  );
}

/** Botão azul principal (atalho para <Botao variante="azul">). */
export function BotaoPrimario(props) {
  return <Botao variante="azul" {...props} />;
}

/** Link com cara de botão. Ex.: <LinkBotao para="/nova-vaga">Nova vaga</LinkBotao> */
export function LinkBotao({ para, variante = "azul", className = "", children, ...props }) {
  return (
    <Link to={para} className={`${BASE_BOTAO} ${VARIANTES[variante]} ${className}`} {...props}>
      {children}
    </Link>
  );
}

/** Caixa vermelha para erros gerais. Com `aoTentarDeNovo`, mostra o botão "Tentar de novo". */
export function AvisoErro({ children, aoTentarDeNovo }) {
  if (!children) return null;
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
    >
      <span>{children}</span>
      {aoTentarDeNovo && (
        <button
          type="button"
          onClick={aoTentarDeNovo}
          className="inline-flex cursor-pointer items-center gap-1.5 font-semibold underline-offset-2 hover:underline"
        >
          <RotateCw className="size-3.5" aria-hidden="true" />
          Tentar de novo
        </button>
      )}
    </div>
  );
}

/**
 * Grupo de opções em formato de chip (rádio por baixo, então funciona no teclado).
 * opcoes = [{ valor, rotulo }]
 */
export function OpcoesChip({ nome, legenda, opcoes, valor, aoMudar, desabilitado = false }) {
  return (
    <fieldset disabled={desabilitado} className="min-w-0">
      <legend className="sr-only">{legenda}</legend>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-slate-600" aria-hidden="true">
          {legenda}:
        </span>
        {opcoes.map((opcao) => {
          const marcado = valor === opcao.valor;
          return (
            <label key={opcao.valor} className={desabilitado ? "cursor-not-allowed" : "cursor-pointer"}>
              <input
                type="radio"
                name={nome}
                value={opcao.valor}
                checked={marcado}
                onChange={() => aoMudar(opcao.valor)}
                className="peer sr-only"
              />
              <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 transition peer-checked:border-blue-600 peer-checked:bg-blue-50 peer-checked:font-medium peer-checked:text-blue-700 peer-focus-visible:ring-2 peer-focus-visible:ring-blue-600/40 peer-disabled:opacity-60 hover:border-slate-400">
                {marcado && <CircleCheck className="size-3.5" aria-hidden="true" />}
                {opcao.rotulo}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
