# Projeto3_tecweb

## Cronograma

Legenda de tamanho: XS, S, M, L, XL (os mesmos usados no quadro do GitHub Projects).
Níveis do produto: **Núcleo** (análise vaga × currículo), **Meio-termo** (preferências e sugestões de busca) e **Extra** (vagas reais via API pública).

### Sprint 1 (10/11 a 13/11): fluxo principal funcionando de ponta a ponta

**Setup e entregáveis do enunciado**
- [X] Validar a proposta com a Bárbara (XS)
- [X] Criar o repositório e adicionar a `BarbaraTieko` (XS)
- [X] Criar o quadro "Team Planning" no GitHub Projects com To Do, Doing e Done; cada tarefa com responsável, tamanho, data de início e data de fim (S)
- [ ] Desenhar o fluxo de telas de baixa fidelidade e salvar a imagem em `docs/` (M)
- [X] Criar o esqueleto do Django REST Framework e do React (Vite), com `.env.example` e CORS (S)
- [X] Escolher e configurar o framework CSS: Tailwind (S)
- [ ] Fazer o deploy inicial (backend e frontend) e colocar o link no README (M)
- [ ] Gerar a chave da API do Gemini e guardá-la em variável de ambiente (XS)

**Conta de usuário**
- [X] Endpoints de cadastro, login e logout (M)
- [X] Telas de cadastro e login, com rotas protegidas no React (M)

**Núcleo: currículo, vagas e análise**
- [X] Criar os modelos `Perfil`, `Curriculo`, `Vaga` e `Analise` (S)
- [X] API de CRUD de vagas, com status (interessado, candidatado, entrevista, oferta, encerrada) (M)
- [ ] Tela para o usuário colar o texto do currículo (M)
- [ ] IA: estruturar o currículo em JSON e guardar em cache (M)
- [ ] IA: endpoint de análise da vaga com prompt, schema de saída e validação no serializer (L)
- [ ] Cache da análise por par (currículo, vaga) (S)
- [ ] Tela de nova vaga (colar o texto) e tela de resultado da análise (L)
- [ ] Kanban básico de vagas: listar por status e mover entre colunas (M)
- [ ] Deploy com o fluxo principal funcionando (S)
- [ ] Responder o questionário de equipe da Sprint 1 (XS)

### Sprint 2 (16/11 a 19/11): acabamento, meio-termo e diferencial

**Núcleo: finalização**
- [ ] IA: gerar carta de apresentação usando só fatos do currículo, com edição pelo usuário (M)
- [ ] Tratar erros da IA (limite de requisições, JSON inválido, tempo esgotado) e estados de carregamento (M)
- [ ] Aviso de privacidade sobre o envio do currículo à API de IA (XS)
- [ ] Aplicar o framework CSS em todas as telas (L)
- [ ] Testes do backend: autenticação, vagas e análise com a IA simulada (mock) (M)

**Meio-termo: preferências e sugestões**
- [ ] Modelo e endpoint de preferências (áreas, tipo da vaga, modalidade, cidade, stack, o que evitar) (S)
- [ ] Tela de preferências no perfil (M)
- [ ] Usar as preferências no prompt da análise e da carta (S)
- [ ] Filtro do kanban pelas preferências (S)
- [ ] IA: sugerir áreas, cargos e palavras-chave de busca a partir do currículo e das preferências (M)
- [ ] Gerar links de busca prontos com essas palavras-chave (S)

**Extra (só se sobrar tempo; é o primeiro item a cortar)**
- [ ] Verificar cobertura para o Brasil e limites gratuitos de uma API pública de vagas (S)
- [ ] Integrar a API e listar vagas reais (L)
- [ ] IA: ranquear as vagas pela aderência ao perfil (M)
- [ ] Botão "salvar no kanban" nas vagas listadas (S)

**Diferencial (A+)**
- [ ] Montar um conjunto com cerca de 10 pares currículo × vaga (M)
- [ ] Comparar duas versões do prompt nesse conjunto e registrar o resultado no README (M)
- [ ] Teste rápido com cerca de 5 usuários e registro do retorno no README (M)
- [ ] Responder o questionário de equipe da Sprint 2 (XS)

### Fechamento (20/11 a 23/11)
- [ ] Congelar funcionalidades em 20/11 (XS)
- [ ] README completo: proposta, público-alvo, como rodar backend e frontend, variáveis de ambiente, link do deploy, fluxo de telas e uso de IA (M)
- [ ] Revisar o quadro: todas as tarefas com responsável, tamanho, datas e passagem por To Do, Doing e Done (S)
- [ ] Conferir que todos os integrantes têm commits significativos (XS)
- [ ] Testar o deploy do zero com uma conta nova (S)
- [ ] Preparar a apresentação, incluindo o exemplo concreto de uso de IA no desenvolvimento: o que queríamos, como usamos a IA, o que corrigimos e como verificamos (M)
- [ ] Ensaiar a apresentação (S)
- [ ] Último commit antes das 09:30 de 24/11 (XS)

### Apresentação: 24/11/2026

## Estrutura do repositório

```
backend/    Django REST Framework (projeto "encaixe")
  contas/   Perfil, cadastro, login e logout
  vagas/    Curriculo, Vaga, Analise e o CRUD de vagas
frontend/   React (Vite) + Tailwind
  src/api.js            axios já com o endereço do backend e o token
  src/auth/             login no React (useAuth, RotaProtegida)
  src/components/       Layout com menu lateral, campos de formulário...
  src/pages/            uma tela por arquivo
```

## Como rodar localmente

Precisa de Python 3.11+ e Node.js 20+. Rode o backend e o frontend em dois terminais.

**Backend** (http://127.0.0.1:8000)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (no Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env  (depois preencha o .env)
python manage.py migrate
python manage.py createsuperuser   # opcional, para usar o /admin
python manage.py runserver
```

**Frontend** (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

O frontend chama `http://127.0.0.1:8000/api` por padrão. Para mudar, crie `frontend/.env` a partir do `frontend/.env.example`.

## Variáveis de ambiente

Os valores ficam em `backend/.env` (local) ou no painel do Render (deploy). O `.env` nunca vai para o Git.

| Variável | Para que serve |
| --- | --- |
| `SECRET_KEY` | chave secreta do Django |
| `DEBUG` | `True` só na máquina local |
| `ALLOWED_HOSTS` | domínios aceitos, separados por vírgula |
| `CORS_ALLOWED_ORIGINS` | endereços do frontend que podem chamar a API |
| `DATABASE_URL` | PostgreSQL do Render (vazio = SQLite local) |
| `GEMINI_API_KEY` | chave da API do Gemini (Google AI Studio) |
| `VITE_API_URL` | (frontend) endereço da API, terminando em `/api` |

## API

Todas as rotas, menos cadastro e login, exigem o cabeçalho `Authorization: Token <token>`. No React, use o `api` de `src/api.js`, que já manda o token.

| Método | Rota | O que faz | Resposta |
| --- | --- | --- | --- |
| POST | `/api/auth/cadastro/` | cria conta: `{nome, email, senha}` | 201 `{token, usuario}` |
| POST | `/api/auth/login/` | entra: `{email, senha}` | 200 `{token, usuario}` |
| POST | `/api/auth/logout/` | invalida o token | 204 |
| GET | `/api/auth/eu/` | usuário logado | 200 `{id, nome, email}` |
| GET | `/api/vagas/` | lista as vagas do usuário (filtro opcional `?status=entrevista`) | 200 |
| POST | `/api/vagas/` | cria vaga: `{titulo, empresa, descricao, local?, link?, status?}` | 201 |
| GET | `/api/vagas/<id>/` | detalhe da vaga | 200 |
| PUT / PATCH | `/api/vagas/<id>/` | edita a vaga (PATCH `{status}` move no kanban) | 200 |
| DELETE | `/api/vagas/<id>/` | apaga a vaga | 204 |

Status da vaga: `interessado`, `candidatado`, `entrevista`, `oferta`, `encerrada`. Cada vaga traz `ultima_nota` (0 a 100, ou `null` se ainda não foi analisada). Erros de validação voltam com 400 no formato `{campo: ["mensagem"]}`; vaga de outro usuário responde 404.

Próximos endpoints (sugestão para as tarefas de IA, podem mudar):

| Método | Rota | O que faz |
| --- | --- | --- |
| GET / PUT | `/api/curriculo/` | lê e salva o texto do currículo; ao salvar, a IA estrutura em JSON |
| POST | `/api/vagas/<id>/analise/` | analisa a vaga com a IA (usa o cache se currículo e vaga não mudaram) |
| GET | `/api/vagas/<id>/analise/` | última análise da vaga |
