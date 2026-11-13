import EmConstrucao from "../components/EmConstrucao";

// Formulário: POST /api/vagas/ com { titulo, empresa, link, descricao, status }.
export default function NovaVaga() {
  return <EmConstrucao titulo="Nova vaga" tarefa="Tela de nova vaga (colar o texto)" />;
}
