import { LoaderCircle } from "lucide-react";

/** Spinner centralizado. `dentroDoLayout` usa meia tela em vez da tela inteira. */
export default function TelaCarregando({ dentroDoLayout = false }) {
  return (
    <div
      className={`grid place-items-center ${dentroDoLayout ? "min-h-[50vh]" : "min-h-screen"}`}
      role="status"
    >
      <LoaderCircle className="size-6 animate-spin text-blue-600" aria-hidden="true" />
      <span className="sr-only">Carregando</span>
    </div>
  );
}
