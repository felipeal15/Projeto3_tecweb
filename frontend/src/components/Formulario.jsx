// Peças de formulário no estilo do fluxo de telas. Reaproveite nas outras telas.

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
        className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-900 shadow-xs outline-none transition placeholder:text-slate-400 focus:ring-2 focus:ring-blue-600/20 ${
          erro ? "border-red-400 focus:border-red-500" : "border-slate-300 focus:border-blue-600"
        }`}
        {...props}
      />
      {(erro || dica) && (
        <p id={idAjuda} className={`mt-1.5 text-xs ${erro ? "text-red-600" : "text-slate-500"}`}>
          {erro || dica}
        </p>
      )}
    </div>
  );
}

/** Botão azul principal. Com `carregando`, fica desabilitado e mostra `textoCarregando`. */
export function BotaoPrimario({ carregando, textoCarregando, children, className = "", ...props }) {
  return (
    <button
      disabled={carregando}
      className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-xs transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
      {...props}
    >
      {carregando ? textoCarregando : children}
    </button>
  );
}

/** Caixa vermelha para erros gerais (ex.: "E-mail ou senha incorretos."). */
export function AvisoErro({ children }) {
  if (!children) return null;
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
    >
      {children}
    </div>
  );
}
