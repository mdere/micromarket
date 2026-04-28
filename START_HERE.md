# START HERE

Use this file when starting a fresh Codex or AI assistant context for micromarket.

## Read First

Before making changes, read these files in order:

1. `docs/summary/current-state.md`
2. `docs/summary/operating-guide.md`
3. `docs/12-implementation-roadmap.md`
4. Relevant source files for the task

Then validate the repository state against recent commits:

```bash
git status --short
git log --oneline -n 8
git show --stat --summary HEAD
```

If the docs and commits disagree, trust committed code first, inspect the code, then update the docs once the true state is clear.

## Reusable Prompt

Copy and paste this into a new context:

```text
You are working in the micromarket repository.

Please start by reading:

1. docs/summary/current-state.md
2. docs/summary/operating-guide.md
3. docs/12-implementation-roadmap.md

Then run or inspect:

- git status --short
- git log --oneline -n 8
- git show --stat --summary HEAD

Compare the recent commits against the summary before making changes. If they disagree, trust committed code first, inspect the relevant implementation, and update the summary after the true state is clear.

Follow the operating guide:

- keep the MVP local-first and research-only,
- avoid buy/sell/hold advice,
- preserve data/model lineage,
- use provider interfaces for external APIs,
- keep notebooks exploratory and promote stable logic into tested backend modules,
- use fake providers in tests for network-dependent services,
- run tests/lint before commit,
- make comprehensive commits at clean milestones,
- update docs/summary/current-state.md whenever project state or next steps change.

Current intended next work should come from the "Next Recommended Work" and "Future Session Checklist" sections in docs/summary/current-state.md unless I give newer instructions.
```

## Current North Star

Build a local-first AI/ML stock research system that can ingest article evidence, combine it with market data, produce confidence-oriented forecasts, and later evaluate those forecasts against actual outcomes and simple baselines.

The product is decision support only. It must not produce direct buy/sell/hold instructions in the MVP.

## Current Build Direction

As of the latest handoff, the backend vertical slice has:

- analysis persistence,
- manual article artifact storage,
- notebook research workspace,
- `yfinance` market quote provider and quote persistence,
- baseline sentiment provider and sentiment persistence,
- baseline forecast provider and forecast persistence,
- evaluation refresh and summary over persisted forecast outcomes,
- URL article ingestion through a provider boundary,
- article relevance, duplicate handling, and extraction failure reporting,
- minimal UI over the stable analysis API response,
- ticker-centered analysis history in the UI/API,
- API error states and evaluation summary visibility in the UI,
- evaluation refresh controls and dashboard component structure.

The next major step is UI polish around panel-level loading states and clearer failed-analysis detail.
