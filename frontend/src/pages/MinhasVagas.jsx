import EmConstrucao from "../components/EmConstrucao";

// Kanban: GET /api/vagas/ e PATCH /api/vagas/<id>/ com { status } para mover de coluna.
export default function MinhasVagas() {
  return <EmConstrucao titulo="Minhas vagas" tarefa="Kanban básico de vagas" />;
}
