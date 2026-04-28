# micromarket Operating Guide

Last updated: 2026-04-26

This guide is the durable instruction set for future Codex sessions. Read it with `docs/summary/current-state.md` before making changes.

## North Star

Build a local-first AI/ML stock research system that can ingest article evidence, combine it with market data, produce confidence-oriented forecasts, and measure those forecasts later against actual outcomes and simple baselines.

The product is research-only decision support. It must not give direct buy/sell/hold instructions in the MVP.

The highest-risk work is data/model quality, lineage, explainability, and evaluation. Prioritize the trustworthy backend/data pipeline before UI polish.

## Session Start Protocol

At the start of every resumed session:

1. Read `docs/summary/current-state.md`.
2. Read this operating guide.
3. Check recent commits:
   - `git status --short`
   - `git log --oneline -n 8`
   - inspect the latest relevant commit with `git show --stat --summary HEAD`
4. Compare the git log with `current-state.md`.
5. If the summary and commits disagree, trust committed code first, then update the summary once the true state is clear.
6. Inspect the relevant code before implementing. Do not rely only on the docs.

## Commit Discipline

Make comprehensive commits at clean milestones. Prefer committing after each coherent vertical slice, especially when tests pass and docs are updated.

A good commit should include:

- source changes,
- migrations if schema changed,
- tests,
- README or architecture docs if behavior changed,
- `docs/summary/current-state.md` updates when the project state or next step changed.

Before committing:

1. Run `git status --short`.
2. Review `git diff --stat`.
3. Run `git diff --check`.
4. Run relevant tests and lint.
5. Inspect untracked files so local runtime artifacts are not committed accidentally.
6. Stage only intentional files.
7. Use a descriptive commit subject and body.

Recommended commit message shape:

```text
Short imperative subject

Explain the main implementation change.

Explain persistence/API/docs/test impacts.

Mention validation or important constraints when helpful.
```

## Current Validation Commands

Backend:

```bash
cd services/api
source .venv/bin/activate
python -m pytest
python -m ruff check app tests
alembic upgrade head
```

Notebook dependencies are optional:

```bash
cd services/api
source .venv/bin/activate
python -m pip install -e ".[dev,notebooks]"
```

Frontend validation should be added once active UI work resumes.

## Architecture Guardrails

- Keep the MVP local-first.
- Keep Next.js as the UI/orchestration layer.
- Keep FastAPI/Python as the ingestion, market data, sentiment, forecast, and evaluation API.
- Keep PostgreSQL as the structured system of record.
- Keep local filesystem storage for raw artifacts, model artifacts, and reports.
- Keep Jupyter notebooks as exploratory research tools, not production runtime.
- Keep Go out of the MVP critical path until a measured service boundary justifies it.
- Use provider protocols so external APIs do not leak across the app.

## Data And Model Guardrails

- Preserve lineage for every analysis, article, market quote, sentiment run, forecast run, and outcome.
- Store model/provider name and version with every sentiment and forecast output.
- Store limitations with every forecast and analysis response.
- Penalize weak evidence, single-article evidence, stale evidence, and conflicting sentiment.
- Compare forecasts against naive baselines.
- Treat early forecasts as experiments until evaluation proves signal.
- Promote stable notebook logic into tested backend modules before the API depends on it.

## API Guardrails

- Keep MVP language research-only and non-advisory.
- Avoid direct buy/sell/hold outputs.
- Tests should use fake providers for network-dependent services.
- Provider failures should return clear errors and should not corrupt persisted lineage.
- Route responses should expose enough metadata to evaluate and debug the pipeline.

## Database And Migration Guardrails

- Use Alembic for schema changes.
- Keep migrations portable where reasonable; SQLite migration checks are useful even though runtime target is PostgreSQL.
- Never modify existing migrations casually after they are committed unless the project has not shared/applied them and the reason is explicit.
- Add indexes for lookup paths that are already used by the API.

## Git And Workspace Safety

- Never revert user changes unless explicitly asked.
- Treat untracked local data, caches, notebooks checkpoints, and generated artifacts as suspicious until inspected.
- Update `.gitignore` when running the app creates local artifacts in predictable locations.
- Do not commit secrets, API keys, local credentials, personal financial context, or generated runtime data.

## Documentation Guardrails

Update docs when behavior or decisions change:

- `services/api/README.md` for API setup, runtime behavior, provider behavior, and sample requests.
- `notebooks/README.md` for notebook workflow changes.
- `docs/summary/current-state.md` for current implementation state and next recommended work.
- Architecture/roadmap docs when decisions change, not for every small implementation detail.

## Current Build Direction

Continue the first backend vertical slice:

1. Analysis persistence: done.
2. Manual text artifact storage: done.
3. Notebook research workspace: done.
4. Market quote provider and persistence: done.
5. Baseline sentiment provider and persistence: done.
6. Baseline forecast service and persisted forecast records: done.
7. Evaluation refresh and summary: done.
8. URL ingestion: done.
9. Next: article relevance, duplicate handling, and extraction failure reporting.
10. Then: minimal UI over the stable API response.

## Escalation Triggers

Pause and ask the user before:

- changing the approved architecture,
- adding paid services,
- adding a new runtime/service such as Go, Redis, or a queue,
- introducing direct investment advice language,
- changing committed migration history,
- deleting or reverting user work.
