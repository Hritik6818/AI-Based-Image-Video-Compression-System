# Screencast script (2–3 min) + Email template

I can't record your screen or send mail from here — use this script with OBS/Xbox Game Bar, then send the template.

## Recording (120–180s)
1. (0–15s) Show `http://localhost:8000`, `README.md` targets (10MB→2MB, 50MB→15MB).
2. (15–60s) Upload photo → AI mode → point to score/10, SSIM≥0.95, saving%, ms, explanation string.
3. (60–100s) Repeat with Fixed → show `runs/bench_*/report.md` table, AI wins on score.
4. (100–130s) Upload short video → note seconds (not ms — honest latency), show size drop.
5. (130–160s) Show `/api/jobs` + `db/jobs.db` rows (DB proof), `docs/FLOW.md` diagram.
Save as `demo.mp4`, attach + link repo + Render URL.

## Email template
```
Subject: AI Compression System — demo, repo + Render link, docs

Hi [Name],
Demo video attached (demo.mp4) + repo: [github link] + live: [render link].
What it does: AI-adaptive image/video compression (SSIM≥0.95 target), auto retry, 1–10 benchmark, AI vs fixed report.
How to use: see docs/HOW_TO_USE.md (pip install → make_samples → benchmark → uvicorn → open :8000).
Results: see runs/bench_*/report.md (AI score vs fixed). Full docs: PRD.md, docs/ARCHITECTURE.md, FLOW.md, ALGORITHM.md, BENCHMARK_SCALE.md, RESEARCH.md, DEPLOY_RENDER.md.
Note: image latency ~100–400ms; full video transcode is seconds (ffmpeg-bound). DB: sqlite jobs table.
Thanks, [You]
```
Attach: `demo.mp4`, `README.md`, `docs/HOW_TO_USE.md`, latest `runs/bench_*/report.md`.
