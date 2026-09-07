# PaperworkPilot Week 4 repository upload

Upload the contents of the prepared repository folder to the root of a public GitHub repository. Do not upload the ZIP as a nested file.

## Include

- `agent/` — LangGraph state, schemas, tools, prompts, routing, and demo fixtures
- `backend/` — FastAPI application and file intake routes
- `public/` — frontend application, styles, and favicon
- `evaluation/` — 40-case golden dataset, evaluators, LangSmith runner, judge, and report generator
- `docs/` — project, architecture, evaluation, and Week 4 design documentation
- `samples/` — fictional demonstration forms
- `test/` — API, agent, UI, and Week 4 evaluation tests
- `assets/` — demo animation
- `submission/` — Week 4 runbook and documentation artifact
- `README.md`, `LIVE_DEMO.md`, `SECURITY.md`
- `.replit`, `replit.nix`, `requirements.txt`, `.env.example`, `.gitignore`

## Keep out

- `.env` and all API keys or tokens
- `__pycache__/`, `.venv/`, `node_modules/`, `.pnpm-store/`
- `sources/` and local project-sync files
- temporary `serve_*_tmp.js` files
- intermediate sync ZIPs
- local LangSmith result JSON and generated output folders
- personal paperwork or real customer data

## Verification before making the repository public

```bash
python -m unittest discover -s test -v
python -m evaluation.run_evals
```

Then confirm the README's live application link, public repository URL, and Week 4 LangSmith experiment link open without authentication. Add API keys only as Replit/GitHub Actions secrets, never as repository files.
