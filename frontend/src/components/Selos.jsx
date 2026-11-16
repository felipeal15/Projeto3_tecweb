import { Sparkles } from "lucide-react";
import { nivelNota } from "../vagas";

/** Etiqueta roxa "Gerado por IA". */
export function SeloIA() {
  return (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-violet-300 bg-violet-50 px-2 py-0.5 text-[11px] font-medium text-violet-700">
      <Sparkles className="size-3" aria-hidden="true" />
      Gerado por IA
    </span>
  );
}

/** "86% · Alta" colorido conforme a nota; "Sem análise" se ainda não foi analisada. */
export function SeloNota({ nota }) {
  if (nota === null || nota === undefined) {
    return (
      <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
        Sem análise
      </span>
    );
  }
  const nivel = nivelNota(nota);
  return (
    <span className={`rounded-md px-2 py-0.5 text-xs font-semibold ${nivel.fundo} ${nivel.texto}`}>
      {nota}% · {nivel.rotulo}
    </span>
  );
}
