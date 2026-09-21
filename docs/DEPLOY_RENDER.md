# Deploy on Render (free tier)

Render can't be deployed from here without your account — these files + steps do it in ~10 min.

## Files included
- `render.yaml`: one web service (python, `pip install -r requirements.txt`, `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`), includes ffmpeg via `apt`? Render native env lacks apt — so use **Docker** deploy instead (see Dockerfile, ffmpeg preinstalled).
- `Dockerfile`: `python:3.11-slim + ffmpeg + uvicorn`, serves frontend + API on `$PORT`.

## Steps
1. Push this folder to GitHub (see `docs/GITHUB.md`).
2. Render → New → Web Service → select repo → **Docker** runtime.
3. Settings: instance Free; env `DB_PATH=/var/data/jobs.db`; add Disk `/var/data` 1GB (needed or sqlite resets).
4. Deploy → open `https://<app>.onrender.com` (UI at `/`, health at `/health`).
5. Optional Postgres: Render → New Postgres → copy `DATABASE_URL`; adapt `src/db.py` (psycopg) — sqlite is fine for demo.

## Limits on free tier
- Cold starts ~30–60s; video transcodes >30s may hit timeout — keep uploads <50MB, prefer images for demo.
- No GPU: neural codecs (DCVC) not deployable here; H.264-adaptive is the correct choice.
