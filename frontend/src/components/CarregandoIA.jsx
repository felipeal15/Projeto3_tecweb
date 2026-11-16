import { LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

/**
 * Card mostrado enquanto a IA trabalha. Conta os segundos para o usuário
 * saber que a página não travou (a chamada leva de 5 a 30 s).
 */
export default function CarregandoIA({ titulo, descricao }) {
  const [segundos, setSegundos] = useState(0);

  useEffect(() => {
    const relogio = setInterval(() => setSegundos((s) => s + 1), 1000);
    return () => clearInterval(relogio);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-xl border border-violet-200 bg-violet-50/70 px-6 py-8 text-center"
    >
      <LoaderCircle className="mx-auto size-7 animate-spin text-violet-600" aria-hidden="true" />
      <p className="mt-3 font-semibold text-slate-900">{titulo}</p>
      {descricao && <p className="mx-auto mt-1 max-w-md text-sm text-slate-600">{descricao}</p>}
      <p className="mt-3 text-xs text-slate-500" aria-hidden="true">
        {segundos < 20
          ? `${segundos} s · costuma levar de 10 a 20 segundos`
          : `${segundos} s · está demorando um pouco mais que o normal, aguarde`}
      </p>
    </div>
  );
}
