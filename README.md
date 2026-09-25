# CoalMind

Document intelligence for CMPDI / Coal India (SIH 26023). Team AGNIVAULT.

Upload mining reports → extract text and metrics → ask in English → see the source page → flag conflicting numbers → download a brief.

## Run locally

API (from this folder, with `backend` on `PYTHONPATH`):

```text
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

UI:

```text
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 (proxies `/api` to port 8000).

After `npm run build`, the API also serves the UI at http://127.0.0.1:8000 when `frontend/dist` exists.

## Production UI

Set `VITE_API_URL` to the public FastAPI origin before `npm run build` / Vercel.

Do not commit `.env` or `backend/storage`.

## Supabase

1. Copy `.env.example` to `.env` and set `SUPABASE_URL` + service role as `SUPABASE_KEY`.
2. In the SQL editor (or `python backend/database/link_supabase.py` if a Management API token is present), run `backend/database/migrations.sql`.
3. Set `STORE_TYPE=supabase`. `/health` should report `"store": "supabase"`.

SQLite is still used if the cloud keys are missing.
