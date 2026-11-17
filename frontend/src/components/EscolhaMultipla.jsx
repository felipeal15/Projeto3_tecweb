import { CircleCheck, Plus } from "lucide-react";
import { useState } from "react";

/**
 * Chips de múltipla escolha (checkbox por baixo, então funciona no teclado).
 * opcoes = [{ valor, rotulo }] ou ["Texto"]. Com `permitirOutro`, o usuário digita
 * itens que não estão na lista (ex.: uma área ou tecnologia diferente).
 */
export default function EscolhaMultipla({
  id,
  legenda,
  opcoes,
  valores,
  aoMudar,
  permitirOutro = false,
  placeholderOutro = "Outro...",
  limite,
  erro,
}) {
  const [outro, setOutro] = useState("");
  const normalizadas = opcoes.map((opcao) =>
    typeof opcao === "string" ? { valor: opcao, rotulo: opcao } : opcao,
  );
  const mesmo = (a, b) => a.toLocaleLowerCase("pt-BR") === b.toLocaleLowerCase("pt-BR");
  // Itens que o usuário digitou aparecem como chips marcados, depois das opções da lista.
  const extras = valores
    .filter((valor) => !normalizadas.some((opcao) => mesmo(opcao.valor, valor)))
    .map((valor) => ({ valor, rotulo: valor }));
  const todas = [...normalizadas, ...extras];
  const cheio = limite !== undefined && valores.length >= limite;

  function alternar(valor) {
    aoMudar(valores.includes(valor) ? valores.filter((v) => v !== valor) : [...valores, valor]);
  }

  function adicionarOutro() {
    const texto = outro.trim().replace(/\s+/g, " ");
    if (!texto || cheio) return;
    const existente = todas.find((opcao) => mesmo(opcao.valor, texto));
    if (existente) {
      if (!valores.includes(existente.valor)) aoMudar([...valores, existente.valor]);
    } else {
      aoMudar([...valores, texto]);
    }
    setOutro("");
  }

  return (
    <fieldset className="min-w-0">
      <legend className="mb-2 text-sm font-medium text-slate-700">{legenda}</legend>
      <div className="flex flex-wrap items-center gap-2">
        {todas.map((opcao) => {
          const marcado = valores.includes(opcao.valor);
          const bloqueado = !marcado && cheio;
          return (
            <label key={opcao.valor} className={bloqueado ? "cursor-not-allowed" : "cursor-pointer"}>
              <input
                type="checkbox"
                name={id}
                value={opcao.valor}
                checked={marcado}
                disabled={bloqueado}
                onChange={() => alternar(opcao.valor)}
                className="peer sr-only"
              />
              <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 transition peer-checked:border-blue-600 peer-checked:bg-blue-50 peer-checked:font-medium peer-checked:text-blue-700 peer-focus-visible:ring-2 peer-focus-visible:ring-blue-600/40 peer-disabled:opacity-50 hover:border-slate-400">
                {marcado && <CircleCheck className="size-3.5" aria-hidden="true" />}
                {opcao.rotulo}
              </span>
            </label>
          );
        })}

        {permitirOutro && (
          <span className="inline-flex items-center rounded-full border border-dashed border-slate-300 bg-white pl-3 focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-600/20">
            <label htmlFor={`${id}-outro`} className="sr-only">
              Adicionar em {legenda}
            </label>
            <input
              id={`${id}-outro`}
              value={outro}
              onChange={(e) => setOutro(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault(); // Enter adiciona o item em vez de enviar o formulário
                  adicionarOutro();
                }
              }}
              maxLength={40}
              disabled={cheio}
              placeholder={cheio ? `Limite de ${limite}` : placeholderOutro}
              className="w-28 bg-transparent py-1.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
            />
            <button
              type="button"
              onClick={adicionarOutro}
              disabled={cheio || !outro.trim()}
              aria-label={`Adicionar em ${legenda}`}
              className="cursor-pointer rounded-full p-1.5 text-blue-600 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
            >
              <Plus className="size-4" aria-hidden="true" />
            </button>
          </span>
        )}
      </div>
      {erro && <p className="mt-1.5 text-xs text-red-600">{erro}</p>}
    </fieldset>
  );
}
