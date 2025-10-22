# Admin Clientes — CRUD, Listagem, Relatórios (Python + PostgreSQL)

Sistema de administração de clientes com foco em limpeza visual, responsividade e boas práticas de UX/UI, atendendo aos requisitos de validação, categorização por renda e relatórios em cards com filtros de período.

## Sumário

- Visão geral e requisitos
- Tecnologias e dependências
- Guia rápido (Local)
- Guia detalhado (Local e Produção)
- Variáveis de ambiente (configuração)
- Estrutura de pastas e rotas
- Funcionalidades e regras de negócio
- Relatórios (definições e filtros)
- Teste manual e dados de exemplo
- Troubleshooting (erros comuns)
- Decisões técnicas e próximos passos

## Visão geral

O sistema permite:
- Cadastrar clientes (inserir, editar, excluir);
- Pesquisar por nome;
- Ver renda em badge customizada (cores por classe A/B/C);
- Gerar relatórios com cards e filtros (hoje, semana, mês, todos).

Banco de dados relacional: PostgreSQL.

## Tecnologias e dependências

- Linguagem: Python 3.x
- Backend/Servidor: WSGI (padrão) com `wsgiref.simple_server` para desenvolvimento
- Banco de Dados: PostgreSQL (driver `psycopg`)
- Frontend: HTML + CSS custom (responsivo) + JS leve
- Dependências Python: ver `requirements.txt`

Requisitos mínimos:
- Python 3.10+
- PostgreSQL 13+

## Guia rápido (Local)

1) Banco (PostgreSQL)
- Crie o banco (escolha uma opção):
  - psql (usuário postgres): `psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE clientes;"`
  - Docker: `docker run --name clientes-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=clientes -p 5432:5432 -d postgres:16`

2) Variáveis de ambiente (uma das formas):
- `export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/clientes"`
  - Windows PowerShell: `$env:DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/clientes"`

3) Ambiente virtual + dependências:
- `sudo apt install -y python3-venv` (se necessário)
- `python3 -m venv .venv && source .venv/bin/activate`
- `python -m pip install --upgrade pip`
- `pip install -r requirements.txt`

4) Rodar o servidor de dev:
- `python run.py`
- Abra `http://127.0.0.1:8000`

Nota: a tabela `clients` é criada automaticamente no primeiro acesso.

## Guia detalhado (Local e Produção)

Desenvolvimento (WSGI básico):
- `python run.py` (hot-reload não incluso; reinicie ao alterar Python)

Produção (exemplo com gunicorn):
- Instale: `pip install gunicorn`
- Comando: `gunicorn -w 2 -b 0.0.0.0:8000 app:application`
- Coloque atrás de um proxy (nginx) e configure logs/timeout conforme seu ambiente.

Banco de dados:
- Tabela `clients` criada automaticamente (DDL idempotente em `init_db`).
- Troca de schema/índices: ajuste em `db.py` se necessário.

## Variáveis de ambiente (configuração)

Prioridade: `DATABASE_URL` (se presente) > `PG*` individuais
- `DATABASE_URL` (recomendado): `postgresql://USUARIO:SENHA@HOST:PORT/DB`
- Alternativa com variáveis:
  - `PGHOST` (padrão: 127.0.0.1)
  - `PGPORT` (padrão: 5432)
  - `PGUSER` (padrão: postgres)
  - `PGPASSWORD` (padrão: postgres)
  - `PGDATABASE` (padrão: clientes)

## Estrutura de pastas e rotas

```
.
├── app.py                      # Rotas WSGI e HTML
├── db.py                       # Persistência (PostgreSQL) e queries
├── run.py                      # Subida do servidor local
├── templates/
│   └── base.html               # Template base
├── static/
│   ├── css/style.css           # Estilos (dark, moderno, responsivo)
│   └── js/main.js              # JS opcional
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md
└── README.md
```

Rotas principais:
- GET `/` → redireciona para `/clients`
- GET `/clients` → lista e busca (query `?q=`)
- GET `/clients/new` → formulário de novo cliente
- POST `/clients` → cria cliente
- GET `/clients/<id>/edit` → formulário de edição
- POST `/clients/<id>/update` → atualiza cliente
- POST `/clients/<id>/delete` → exclui cliente (confirmação no botão)

## Funcionalidades

- CRUD de clientes: inserir, editar, excluir.
- Listagem com pesquisa por nome.
- Renda exibida em badge com cor pela classe:
  - A: ≤ R$ 980,00 (vermelho)
  - B: R$ 980,01 a R$ 2.500,00 (amarelo)
  - C: > R$ 2.500,00 (verde)
- Relatórios em cards com filtros (hoje/semana/mês/todos).

## Regras e validações

HTML5 (formulários):
- Nome: `required`, `maxlength=150`, e deve conter apenas letras (com acentos), espaços, apóstrofo, hífen e ponto.
- CPF: `required`, `pattern="\d{10}"`, `maxlength=10` (somente números, 10 dígitos).
- Data de nascimento: `type=date`, `required`, `max=<hoje>`.
- Data de cadastro: `type=date`, `readonly`, preenchido automaticamente.
- Renda familiar: `type=number`, `min=0`, `step=0.01` (opcional).

Backend:
- Nome: obrigatório, ≤ 150 e regex de caracteres; espaços normalizados.
- CPF: 10 dígitos (somente números) e unicidade no banco.
- Data de nascimento: não pode ser futura.
- Renda: se informada, ≥ 0.

Notas sobre CPF:
- A pedido, o CPF tem no máximo 10 dígitos (somente números). A validação algorítmica do CPF real (11 dígitos) não se aplica neste cenário.

## Relatórios e filtros

- Rota: `GET /reports?period=(today|week|month|all)`.
- Cards:
  - Maiores de 18 com renda > média geral (média calculada sobre todos com renda informada).
  - Quantidade por classe (A, B, C) dentro do período selecionado.
- Período usa a `data_cadastro` do cliente (DATE no Postgres). Opções:
  - `today` (hoje), `week` (segunda até hoje), `month` (1º dia do mês até hoje), `all` (todos)
  - “Maiores de 18 com renda > média” usa: EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) ≥ 18 e renda > AVG(renda) considerando rendas informadas.

## Teste manual e dados de exemplo

1. Criar cliente: “Novo Cliente” → preencha campos → “Salvar”.
2. Editar: “Editar” na listagem → ajuste dados → “Salvar”.
3. Excluir: “Excluir” na listagem (confirmação necessária).
4. Pesquisar: campo “Pesquisar por nome...” na listagem.
5. Relatórios: acesse “Relatórios” e troque o período no seletor.

Dados de exemplo (psql):
```sql
INSERT INTO clients (nome, cpf, data_nascimento, data_cadastro, renda_familiar)
VALUES
('Ana Maria', '1234567890', '1990-05-12', CURRENT_DATE, 900.00),
('Bruno Souza', '1112223334', '1985-02-20', CURRENT_DATE, 1500.00),
('Carla Dias', '2223334445', '2000-10-01', CURRENT_DATE, 3200.00);
```

## Troubleshooting (erros comuns)

- PEP 668 / ambiente gerenciado: crie um venv e rode `pip install -r requirements.txt` dentro dele.
- Conexão Postgres falhou: verifique `DATABASE_URL`, usuário, senha, host e porta; teste com `psql`.
- Porta 5432 em uso (Docker): pare outro Postgres ou use `-p 5433:5432` no `docker run` e ajuste a URL.
- JS/CSS desatualizado (cache): faça hard refresh (Ctrl+F5) ou abra aba anônima.
- Formato de data dd/mm/aaaa: definimos `lang="pt-BR"` no input; alguns navegadores seguem a localidade do SO. Se precisar 100% dd/mm/aaaa, troque o campo para `type="text"` com máscara — posso implementar.

## Decisões técnicas

- Zero dependências para facilidade de execução em qualquer ambiente com Python 3.
- CSS próprio para garantir badge custom e identidade visual clean.
- Roteamento WSGI simples para manter o projeto leve e didático.
- Postgres: `DATE` para datas e `NUMERIC(14,2)` para renda.

## Próximos passos (opcionais)

- Autenticação/Autorização.
- Paginação, ordenação e exportação (CSV/XLSX).
- Docker Compose (app + Postgres), autenticação, paginação/ordenação/exportação, cache busting para estáticos, testes automatizados.
