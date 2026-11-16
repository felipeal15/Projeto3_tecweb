import { ShieldCheck } from "lucide-react";

/**
 * Aviso de que o currículo e a vaga vão para a API do Gemini.
 * A versão completa fica onde o currículo é colado; a `curta`, nas outras telas.
 */
export default function AvisoPrivacidade({ curto = false, className = "" }) {
  return (
    <div
      className={`flex items-start gap-2.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs leading-relaxed text-slate-600 ${className}`}
    >
      <ShieldCheck className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
      {curto ? (
        <p>
          Para gerar a análise e a carta, o texto do seu currículo e o da vaga são enviados à API de
          IA do Google Gemini.
        </p>
      ) : (
        <p>
          <span className="font-medium text-slate-700">Privacidade: </span>
          para gerar a análise e a carta, o texto do seu currículo e o das vagas são enviados à API
          de IA do Google Gemini. No plano gratuito da API, o Google pode usar esse conteúdo para
          melhorar os serviços dele. Antes de colar, tire o que não ajuda na análise, como CPF,
          endereço e telefone.
        </p>
      )}
    </div>
  );
}
