# micromarket

micromarket is an AI-assisted stock research product concept. It ingests company-related articles, extracts sentiment and market-relevant signals, and presents a transparent decision-support view for a selected stock.

This project is not financial advice software and should not make autonomous buy/sell decisions. The product should help a user research, compare signals, and understand uncertainty before making their own investment decision.

## Product Docs

The initial product-management package follows the workflow in `ai_tools/AI-Product-Development-Toolkit`:

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
14. [Session Summary / Handoff](docs/summary/current-state.md)

## Assumptions

- First version is a web application.
- First version supports one selected public company/ticker at a time.
- News/article ingestion starts with public RSS/news APIs or uploaded article URLs, not paid market terminals.
- Prediction outputs must include confidence, evidence, and limitations.
- Any recommendation language must be framed as decision support, not personalized financial advice.
