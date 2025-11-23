# Hi‑Tech VC Valuation

Local notebook + API + React GUI to model VC valuations for the Hi‑Tech assignment, with investor toggle (Galaxy / Acorn), term versioning, sensitivity, and waterfall.

## Prereqs
- Python 3.11+
- Node 18+

## Backend (FastAPI)
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

## Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and ensure the API is running on http://localhost:8000.

## Notebook
Open `calculations.ipynb` in Jupyter. It reuses the backend valuation engine for consistency.

## Term Versions
Seed defaults under `data/terms/{acorn|galaxy}/v1.json`. Active version is in `active.json`. You can create/activate versions via API:
- GET `/api/terms/{investor}` — list versions and active
- POST `/api/terms/{investor}` — create new version (body: `{ version_id, data }`)
- POST `/api/terms/{investor}/activate` — set active `{ version_id }`

## Notes
- Series B is modeled for dilution and investor pro‑rata participation; Series B has no liquidation preference (simplification).
- Dividends are simple cumulative at 10% for Series A; IPO scenarios convert to common (no pref).
- Anti‑dilution hooks are parameterized but off by default.

## Deploying to Vercel
The repo ships with a `vercel.json` that deploys the React UI as a static build and the FastAPI app as a Python serverless function under `/api/*`.

1. Install the Vercel CLI (`npm i -g vercel`) and log in with `vercel login`.
2. From the repo root run `vercel` once to create/link a project. The CLI will pick up `vercel.json`, install `frontend` deps, and build the Vite app.  
3. A workspace-level `package.json` proxies `npm run build` to `frontend`, so Vercel just runs `npm install && npm run build` at the repo root (same as you can do locally to reproduce CI).
4. The Python function (`api/index.py`) reuses `backend.main:app` via `mangum`. All data files under `data/terms/**` are bundled so term versions are available at runtime.
5. Frontend API calls default to the same origin. For local dev continue exporting `VITE_API_BASE=http://localhost:8000` (or add it to `.env`), but no environment variable is needed on Vercel.
6. Use `vercel --prod` when you are ready for production. You can run `vercel dev` locally to exercise the exact serverless/runtime behavior before deploying.



