import EmConstrucao from "../components/EmConstrucao";

// Rota /vagas/:id. Use useParams() para pegar o id e GET /api/vagas/<id>/ para os dados.
export default function AnaliseVaga() {
  return <EmConstrucao titulo="Análise da vaga" tarefa="Tela de resultado da análise" />;
}
