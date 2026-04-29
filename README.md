# micromarket

micromarket is an AI-assisted stock research product concept. It ingests company-related articles, extracts sentiment and market-relevant signals, and presents a transparent decision-support view for a selected stock.

This project is not financial advice software and should not make autonomous buy/sell decisions. The product should help a user research, compare signals, and understand uncertainty before making their own investment decision.

## Product Docs

The initial product-management package follows the workflow in `ai_tools/AI-Product-Development-Toolkit`:

0. [Start Here / AI Handoff Prompt](START_HERE.md)
1. [Product Journey](docs/00-product-journey.md)
2. [Product Requirements Document](docs/01-prd.md)
3. [UX and User Flow Specification](docs/02-ux-user-flow.md)
4. [MVP Concept](docs/03-mvp-concept.md)
5. [MVP Development Plan](docs/04-mvp-development-plan.md)
6. [MVP Test Plan](docs/05-test-plan.md)
7. [v0 Visual Generation Prompt](docs/06-v0-visual-prompt.md)
8. [Product Decisions Questionnaire](docs/07-product-decisions-questionnaire.md)
9. [Architecture Options](docs/08-architecture-options.md)
10. [Technical Architecture](docs/09-technical-architecture.md)
11. [Data Model](docs/10-data-model.md)
12. [Model Evaluation Plan](docs/11-model-evaluation-plan.md)
13. [Implementation Roadmap](docs/12-implementation-roadmap.md)
14. [Model Quality Plan](docs/13-model-quality-plan.md)
15. [Ticker Context Ingestion Plan](docs/14-ticker-context-ingestion-plan.md)
16. [Session Summary / Handoff](docs/summary/current-state.md)
17. [Operating Guide / Guardrails](docs/summary/operating-guide.md)

## Project Structure

```text
apps/web        Next.js SSR dashboard shell
services/api    FastAPI backend scaffold
infra           Docker Compose and environment examples
data            Local raw, processed, artifact, and report storage
docs            Product, architecture, and roadmap documents
```

## Local Development

Create a local Docker Compose environment file:

```bash
cp infra/.env.example infra/.env
```

Start PostgreSQL, API, and web with Docker Compose:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Or run services manually:

```bash
cp services/api/.env.example services/api/.env
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

```bash
cd apps/web
npm install
npm run dev
```

Health check:

```bash
curl http://localhost:8000/health
```

Optional local LLM sentiment:

- The API defaults to deterministic baseline sentiment.
- Ollama can be enabled with `SENTIMENT_PROVIDER=ollama` after Ollama is
  installed, running, and a local model is pulled.
- Full setup and smoke-test instructions live in
  [services/api/README.md](services/api/README.md#ollama-sentiment-provider).

## Assumptions

- First version is a web application.
- First version supports one selected public company/ticker at a time.
- News/article ingestion starts with public RSS/news APIs or uploaded article URLs, not paid market terminals.
- Prediction outputs must include confidence, evidence, and limitations.
- Any recommendation language must be framed as decision support, not personalized financial advice.
