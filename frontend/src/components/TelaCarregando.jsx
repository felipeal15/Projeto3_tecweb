import { LoaderCircle } from "lucide-react";

export default function TelaCarregando() {
  return (
    <div className="grid min-h-screen place-items-center" role="status">
      <LoaderCircle className="size-6 animate-spin text-blue-600" aria-hidden="true" />
      <span className="sr-only">Carregando</span>
    </div>
  );
}
