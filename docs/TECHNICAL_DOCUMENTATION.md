# Documentação Técnica — Sistema de Administração de Clientes

## Visão Geral

Este projeto implementa um sistema completo de administração de clientes com:
- CRUD de clientes (listar, inserir, editar, excluir);
- Pesquisa por nome;
- Exibição de renda em badge com cores por classe (A, B, C) e formatação “R$” sem decimais, com separador de milhar;
- Relatórios em cards com filtros (hoje, semana, mês, todos);
- Validações HTML5 nos formulários e validações de negócio no backend;
- Persistência em base relacional (PostgreSQL).

Frontend, backend e banco foram desenvolvidos com foco em estética limpa, usabilidade e organização de código.

## Arquitetura

- Frontend: HTML + CSS customizado (responsivo, minimalista) e JS opcional (progressive enhancement).
- Backend: Python WSGI com `wsgiref`, roteamento leve e renderização de templates simples.
- Banco de Dados: PostgreSQL (via driver `psycopg`).

Pontos-chave:
- Dependência externa mínima: driver `psycopg`.
- Estrutura modular para facilitar manutenção, com camadas separadas para rotas (app), persistência (db) e apresentação (templates/static).

## Estrutura de Pastas

```
.
├── app.py                      # Aplicação WSGI e rotas
├── db.py                       # Acesso e schema do banco de dados (PostgreSQL)
├── run.py                      # Servidor WSGI local (porta 8000)
├── templates/
│   └── base.html               # Layout base
├── static/
│   ├── css/style.css           # Estilos (dark, moderno, responsivo)
│   └── js/main.js              # JS opcional
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md
└── README.md
```

## Banco de Dados

Tabela `clients` (PostgreSQL):
- `id` SERIAL (PK)
- `nome` VARCHAR(150) NOT NULL
- `cpf` VARCHAR(10) NOT NULL UNIQUE
- `data_nascimento` DATE NOT NULL
- `data_cadastro` DATE NOT NULL DEFAULT CURRENT_DATE
- `renda_familiar` NUMERIC(14,2) NULL

Índices/Restrições:
- `cpf` com `UNIQUE` para evitar duplicidade.

## Regras de Negócio e Validações

- Frontend (HTML5):
- Nome: `required`, `maxlength=150`, apenas letras (com acentos), espaços, apóstrofo, hífen e ponto.
- CPF: `required`, `maxlength=10`, `pattern="\d{10}"` (somente números, 10 dígitos).
- Data de nascimento: `type=date`, `required`, `max=<data atual>`.
- Data de cadastro: `type=date`, `readonly` (preenchido automaticamente na inserção).
- Renda familiar: `type=number`, `step=0.01`, `min=0` (opcional).

- Backend:
- Nome: obrigatório, tamanho máximo 150; validação de caracteres (letras com acentos, espaço, apóstrofo, hífen, ponto) e normalização de espaços.
- CPF: somente dígitos, 10 dígitos; validação de formato; unicidade no banco.
- Data de nascimento: não pode ser futura.
- Renda familiar: se informado, `renda ≥ 0`.

Notas sobre CPF:
- Atendendo à regra explícita, o CPF possui 10 dígitos (somente números). A validação algorítmica do CPF real (11 dígitos) não se aplica.

## Listagem e Pesquisa

- Rota: `GET /clients` com filtro opcional `?q=<nome>`.
- Tabela com colunas: Nome e Renda.
- Renda é exibida em um badge customizado:
  - Classe A (≤ R$ 980,00): fundo vermelho.
  - Classe B (R$ 980,01 a R$ 2.500,00): fundo amarelo.
  - Classe C (> R$ 2.500,00): fundo verde.
- Formatação monetária: `R$` + valor sem decimais, com separador de milhar (ponto).
- Se renda ausente: badge neutro “—”.

## CRUD de Clientes

- Criar: `GET /clients/new` (form), `POST /clients` (salva, define `data_cadastro` com a data atual).
- Editar: `GET /clients/<id>/edit`, `POST /clients/<id>/update`.
- Excluir: `POST /clients/<id>/delete` (com confirmação via `confirm()` no submit).

## Relatórios

- Rota: `GET /reports?period=(today|week|month|all)`.
- Cards:
  1. Quantidade de clientes maiores de 18 anos com renda familiar maior que a renda média de todos os clientes (média calculada sobre todos com renda informada);
  2. Quantidade de clientes por classe (A, B, C) no período selecionado;
  3. Filtro: Hoje, Esta semana, Este mês ou Todos (baseado em `data_cadastro`, tipo DATE no Postgres).

## UI/UX

- Layout dark minimalista, responsivo, com tipografia de sistema.
- Componentes padronizados (botões, campos, cards, table) e espaçamentos consistentes.
- Badges implementados manualmente (sem libs) com cantos arredondados e cores conforme classe.

## Padrões de Código

- Separação de responsabilidades: `app.py` (rotas/HTML), `db.py` (persistência), `static/` e `templates/` (apresentação).
- Nomes claros e funções pequenas.
- Dependência externa mínima (somente driver de banco).

## Pontos de Extensão

- Trocar o motor de templates por Jinja2 (quando desejado).
- Adicionar autenticação e controle de acesso.
- Implementar paginação e ordenação avançada.
- Trocar Postgres por outro SGBD relacional com ajustes em `db.py`.

## Execução (Local / Produção)

Requisitos:
- Python 3.10+
- PostgreSQL 13+

Passos (local):
1) Crie o banco (psql): `psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE clientes;"`
   - Docker alternativo: `docker run --name clientes-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=clientes -p 5432:5432 -d postgres:16`
2) Exporte `DATABASE_URL` ou as variáveis `PG*`:
   - `export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/clientes"`
3) Crie venv e instale deps: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
4) Suba o servidor: `python run.py` e acesse `http://127.0.0.1:8000`

Produção:
- `gunicorn -w 2 -b 0.0.0.0:8000 app:application` atrás de proxy reverso (nginx/apache).
- Configure logs, timeouts, variáveis de ambiente e pool de conexões conforme sua infra.

## Segurança e Considerações
- Saída HTML escapada para evitar XSS.
- Campos validados no frontend (HTML5) e backend (regex e regras de negócio).
- Sem autenticação/CSRF por escopo; se adicionar login, inclua proteção CSRF e sessões.

## Fluxo de Requisições e Renderização
- Roteamento simples em `app.py` mapeia caminhos para handlers.
- `init_db()` é chamado por requisição para garantir schema (idempotente).
- Templates: `templates/base.html` é preenchido por `render_page()` com o corpo específico.
- Estáticos servidos em `/static/*` por `static_app`.

## Consultas e Cálculos
- Busca por nome com `ILIKE` e ordenação por `nome`.
- Relatórios:
  - Média de renda: `AVG(renda_familiar)` considerando registros com renda preenchida.
  - Maiores de 18: `EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) >= 18`.
  - Classes por período: `data_cadastro >= <início>` e contagem por faixas de renda.

## Localização e Datas
- Inputs `type="date"` utilizam o controle nativo do navegador; definido `lang="pt-BR"` e placeholder para dd/mm/aaaa. Se não respeitar, trocar para `type="text"` com máscara no frontend e conversão para ISO no backend.

## Estrutura de Rotas
- `/` → redirect para `/clients`
- `/clients` (GET | POST)
- `/clients/new` (GET)
- `/clients/<id>/edit` (GET)
- `/clients/<id>/update` (POST)
- `/clients/<id>/delete` (POST)
- `/reports` (GET)

## Screenshots (sugestão)

Inclua capturas de tela das páginas: Listagem, Formulário e Relatórios após subir localmente.
