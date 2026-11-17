const PASSOS = ["Conta", "Currículo", "Preferências"];

/** As 3 etapas do cadastro (Conta → Currículo → Preferências). `atual` começa em 0. */
export default function PassosOnboarding({ atual }) {
  return (
    <ol className="flex flex-wrap items-center gap-2 text-xs" aria-label="Etapas do cadastro">
      {PASSOS.map((passo, indice) => {
        const feito = indice < atual;
        const agora = indice === atual;
        return (
          <li key={passo} className="flex items-center gap-2" aria-current={agora ? "step" : undefined}>
            {indice > 0 && (
              <span className={`h-px w-4 ${feito || agora ? "bg-blue-600" : "bg-slate-300"}`} aria-hidden="true" />
            )}
            <span
              className={`grid size-5 place-items-center rounded-full border text-[11px] font-semibold ${
                feito
                  ? "border-blue-600 bg-blue-600 text-white"
                  : agora
                    ? "border-blue-600 text-blue-600"
                    : "border-slate-300 text-slate-400"
              }`}
            >
              {indice + 1}
            </span>
            <span className={agora ? "font-medium text-slate-900" : "text-slate-400"}>{passo}</span>
          </li>
        );
      })}
    </ol>
  );
}
