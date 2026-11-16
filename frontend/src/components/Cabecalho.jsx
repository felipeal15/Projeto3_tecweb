import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * Topo das telas logadas: link de voltar, título, subtítulo e botões à direita.
 * Ex.: <Cabecalho voltar={{ para: "/vagas", rotulo: "Minhas vagas" }} titulo="Nova vaga">...</Cabecalho>
 */
export default function Cabecalho({ voltar, titulo, subtitulo, children }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {voltar && (
          <Link
            to={voltar.para}
            className="mb-2 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:underline"
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            {voltar.rotulo}
          </Link>
        )}
        <h1 className="text-2xl font-bold text-balance text-slate-900">{titulo}</h1>
        {subtitulo && <p className="mt-1 text-sm text-slate-500">{subtitulo}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </header>
  );
}
