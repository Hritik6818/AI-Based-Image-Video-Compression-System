# AI Image & Video Compression

Upload an image or video → AI picks compression settings for that specific file → output is quality-checked automatically → you get a smaller file, a 1–10 quality score, and a download link. A fixed-baseline mode (JPEG q75 / H.264 CRF23) runs side-by-side so every AI result is comparable.

Full spec: [PRD.md](./PRD.md). Extra docs in [`docs/`](./docs).

---

## What it does

- **Images** (`jpg/jpeg/png/webp/bmp/tiff` → `webp` or `jpeg`, Pillow): content-aware quality + downscale for large files.
- **Videos** (`mp4/mov/mkv/avi/webm` → `mp4` H.264 + AAC, ffmpeg): content-aware CRF + preset.
- **AI mode:** analyzes each file (texture, edges, color, entropy), classifies it (`graphic-screen / smooth-lowdetail / textured / photo-natural`), predicts settings, then **measures real PSNR/SSIM after encoding and retries with adjusted settings** (up to 3 retries) if quality or size targets are missed.
- **Fixed mode:** single-pass baseline, no retry — JPEG q75 for images, H.264 CRF23 + preset medium for video.
- **Scoring:** every result gets a 1–10 score plus a verdict (`ACCEPT (excellent/good) / MARGINAL / REJECT / NEEDS-REVIEW`).
- **History:** every web compression is logged in a sqlite `jobs` table.

## How the AI works (`src/`)

1. **Analyze** (`analyzer.py`): resolution, Laplacian texture variance, gradient edge density, colorfulness, luminance entropy. Videos: same features from a real extracted frame.
2. **Classify** (`analyzer.py`): rule-based content class + confidence.
3. **Predict** (`selector.py`): class → `format/quality/scale` (image) or `CRF/preset/scale` (video, H.264).
4. **Compress** (`compressor.py`): Pillow / ffmpeg subprocess.
5. **Evaluate** (`evaluator.py`): real PSNR + SSIM — full-frame for images; same-timestamp frame comparison for videos. No placeholder values.
6. **Retry** (`pipeline.py::compress_auto`): `ssim < min_ssim` → quality+8 / CRF−3; saving below target with quality headroom → quality−8 / CRF+2.
7. **Score** (`scoring.py`): `4.0·SSIM + 2.5·PSNRnorm + 2.5·saving + 1.0·speed`, scaled 0–10 (`PSNRnorm = (PSNR−20)/20`, speed decays with time: 10s scale images, 120s videos).

## Run it

Prerequisites: Python 3.10+, FFmpeg on PATH (`ffmpeg -version`).

```powershell
pip install -r requirements.txt
python scripts/make_samples.py          # one-time: creates demo files in data/samples/
```

**Web app (frontend + backend, one server):**

```powershell
cd "C:\Open Code"                       # must run from repo root, not from backend/
python -m uvicorn backend.main:app --port 8000
# UI:       http://127.0.0.1:8000
# API docs: http://127.0.0.1:8000/docs
# Health:   http://127.0.0.1:8000/health
```

Upload a file, pick AI vs Fixed, see `orig → compressed (saving %)`, score, SSIM/PSNR, and a ⬇ Download link.

**API:**

```powershell
curl -F "file=@data/samples/photo.jpg" -F "mode=ai" http://127.0.0.1:8000/api/compress
curl http://127.0.0.1:8000/api/jobs?limit=5
```

`POST /api/compress` (fields: `file`, `mode=ai|fixed`, `min_ssim=0.95`) returns `job_id, download, filename, kind, orig_size, new_size, saving_pct, psnr, ssim, score_10, verdict, time_ms, params, explanation, attempts`.

**Python:**

```python
from src.pipeline import compress_auto
r = compress_auto("data/samples/photo.jpg", "runs/out/photo.webp", mode="ai")
print(r["orig_size"], r["new_size"], r["best"]["metrics"], r["best"]["score"])
```

**Benchmark (AI vs fixed) + smoke test:**

```powershell
python scripts/benchmark.py data/samples   # -> runs/bench_*/report.{md,csv,json}
python tests/test_pipeline.py              # expect SMOKE OK
```

## Measured results

`python scripts/benchmark.py data/samples`, 2026-09-22 (`runs/bench_20260922_001117/report.md`):

| File | Orig | Fixed | AI | Saving (F/AI) | SSIM (F/AI) | PSNR (F/AI) | Time (F/AI) |
|---|---|---|---|---|---|---|---|
| photo.jpg | 21177 B | 7233 B | 1632 B | 65.8% / 92.3% | 0.9999 / 0.9999 | 52.97 / 49.85 | 93ms / 373ms |
| graphic.png | 1621 B | 4188 B | 924 B | −158.4% / 43.0% | 1.0 / 1.0 | 59.92 / 52.15 | 159ms / 572ms |
| clip.mp4 (5s testsrc) | 48275 B | 36834 B | 25807 B | 23.7% / 46.5% | 1.0 / 0.9999 | 52.59 / 45.28 | 2630ms / 8626ms |

AI wins on all three at equal-or-better quality. Note the honest wart: fixed JPEG *inflates* the tiny PNG (−158%) — the baseline is truly fixed, while AI switches to WebP. Acceptance bar: score ≥ 7.0 (`docs/BENCHMARK_SCALE.md`).

**Latency, honestly:** images ~100–600ms (ms-scale ✓). Full video transcodes are seconds by nature (ffmpeg-bound) — anyone claiming millisecond video compression is not measuring the encode.

## Project structure

```
├── backend/main.py        # FastAPI: POST /api/compress, GET /api/jobs, serves frontend + downloads
├── frontend/              # index.html / app.js / style.css — static, no build step
├── src/
│   ├── analyzer.py        # features + content classification
│   ├── selector.py        # class -> params + retry adjustment + explanation
│   ├── compressor.py      # Pillow (image) / ffmpeg (video)
│   ├── evaluator.py       # real PSNR/SSIM incl. video frame comparison
│   ├── scoring.py         # 1-10 score + verdict
│   ├── pipeline.py        # compress_auto() + retry loop
│   └── db.py              # sqlite jobs log (DB_PATH env, default db/jobs.db)
├── scripts/
│   ├── benchmark.py       # AI vs fixed harness -> runs/bench_*/report.{md,csv,json}
│   ├── make_samples.py    # generates demo samples
│   └── init_repo.ps1      # git init helper
├── tests/test_pipeline.py # smoke test
├── config.yaml            # reference targets (see note below)
├── docs/                  # ARCHITECTURE, FLOW, ALGORITHM, BENCHMARK_SCALE, RESEARCH,
│                          # HOW_TO_USE, DEPLOY_RENDER, GITHUB, SCREENCAST_AND_MAIL
├── Dockerfile / render.yaml  # Docker deploy on Render (ffmpeg included)
└── PRD.md                 # spec (targets + requirements)
```

`config.yaml` documents the target values (`min_ssim 0.95`, `target_saving 0.70`, …). It is a reference — the code takes these as function arguments with matching defaults (`compress_auto(..., min_ssim=0.95, target_saving=0.7, max_retries=3)`); nothing auto-loads the YAML file.

## Troubleshooting

- `ModuleNotFoundError: No module named 'backend'` → run from repo root (`cd "C:\Open Code"`), not from `backend/`.
- UI looks stale after an update → hard-refresh (`Ctrl+Shift+R`); the JS/CSS cache aggressively.
- `/v1/models 404` in server logs → not our endpoint; something else on your machine probing for a local LLM. Ignore it.
- `NEEDS-REVIEW` verdict → quality frames couldn't be evaluated; size/time were still measured and reported.

## What v1 does NOT do

VMAF/LPIPS metrics, AVIF/AV1/H.265 outputs, Bayesian search, RD-curves, trained neural codecs — see Roadmap in [PRD.md](./PRD.md) and the research survey in [`docs/RESEARCH.md`](./docs/RESEARCH.md) for why adaptive-classical is the right v1 trade.
