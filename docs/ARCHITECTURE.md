# Architecture

`frontend (static HTML/JS)` → `backend (FastAPI)` → `src/*` → `db/jobs.db`
Static output served from `runs/out`. Same backend serves UI + API (single Render service).

## Components
- **frontend/**: `index.html/app.js/style.css`, no build step. POSTs `/api/compress`, GETs `/api/jobs`.
- **backend/main.py**: FastAPI; endpoints `POST /api/compress`, `GET /api/jobs`, `GET /health`; mounts `/` (UI) + `/runs/out` (files). Env `DB_PATH`.
- **src/analyzer.py**: PIL+numpy features (texture, edge, color, entropy) + rule classifier.
- **src/selector.py**: class→params (quality/CRF/preset/scale) + retry adjustment + explanation string.
- **src/compressor.py**: Pillow (image) + ffmpeg subprocess (video). Fixed baselines: JPEG q75 / H.264 CRF23 medium.
- **src/evaluator.py**: numpy PSNR + global SSIM (ms latency, no heavy deps).
- **src/scoring.py**: 1–10 composite score + verdict.
- **src/pipeline.py**: `compress_auto()` orchestration + retry loop + ms timing.
- **src/db.py**: sqlite `jobs` table. Render free tier uses disk sqlite; swap `DB_PATH` to Postgres (see DEPLOY_RENDER.md) for scale.
- **scripts/benchmark.py**: folder → AI vs fixed → `report.{json,csv,md}`.

## Request flow
Upload → save `uploads/` → `compress_auto(mode)` → log sqlite → return JSON `{score, ssim, psnr, saving, download}`.
