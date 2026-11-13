import { CircleCheck } from "lucide-react";
import Logo from "./Logo";

const destaques = [
  "Nota de aderência com evidências tiradas do seu currículo",
  "Carta de apresentação que não inventa experiência",
  "Kanban para acompanhar cada candidatura",
];

/** Painel azul-marinho à esquerda das telas de login e cadastro (some em telas pequenas). */
export default function PainelMarca() {
  return (
    <aside className="hidden w-[42%] max-w-xl flex-col justify-between bg-marinho p-10 text-white lg:flex">
      <Logo />

      <div>
        <h1 className="text-3xl leading-tight font-bold">
          Descubra o quanto você combina com cada vaga.
        </h1>
        <p className="mt-4 text-sm leading-relaxed text-blue-100/80">
          Cole a descrição da vaga e a IA compara com o seu currículo: mostra a aderência, o
          que destacar e o que falta.
        </p>
        <ul className="mt-6 space-y-3 text-sm text-blue-50">
          {destaques.map((texto) => (
            <li key={texto} className="flex items-start gap-2.5">
              <CircleCheck className="mt-0.5 size-4 shrink-0 text-blue-300" aria-hidden="true" />
              {texto}
            </li>
          ))}
        </ul>

        <div className="mt-8 rounded-xl border border-white/10 bg-marinho-claro p-4" aria-hidden="true">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">Estágio em Dados · Nuvem Pay</p>
            <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
              86% · Alta
            </span>
          </div>
          <div className="mt-3 h-1.5 rounded-full bg-white/10">
            <div className="h-full w-[86%] rounded-full bg-emerald-400" />
          </div>
          <p className="mt-2 text-xs text-blue-100/70">
            5 de 6 requisitos atendidos · 1 lacuna: Power BI
          </p>
        </div>
      </div>

      <p className="text-xs text-blue-100/60">Projeto 3 · Tecnologias Web · Insper</p>
    </aside>
  );
}
