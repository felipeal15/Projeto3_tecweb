import { Hammer } from "lucide-react";

/** Marcador provisório: troque pela tela de verdade quando a tarefa for feita. */
export default function EmConstrucao({ titulo, tarefa }) {
  return (
    <section>
      <h1 className="text-2xl font-bold text-slate-900">{titulo}</h1>
      <div className="mt-6 flex items-start gap-3 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
        <Hammer className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
        <p>
          Tela ainda não implementada. Tarefa do README:{" "}
          <span className="font-medium text-slate-800">{tarefa}</span>.
        </p>
      </div>
    </section>
  );
}
