export default function Logo({ fundoEscuro = true }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid size-8 place-items-center rounded-lg bg-blue-600 text-sm font-bold text-white">
        E
      </span>
      <span
        className={`text-base font-semibold ${fundoEscuro ? "text-white" : "text-marinho"}`}
      >
        Encaixe
      </span>
    </div>
  );
}
