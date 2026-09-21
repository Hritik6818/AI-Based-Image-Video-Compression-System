# PRD: AI-Based Image & Video Compression System

**Version:** 1.0
**Date:** 2026-09-21
**Status:** Draft for Implementation
**Note:** This PRD is the spec (targets + requirements). Measured implementation status and real numbers live in `README.md` and `runs/bench_*/report.md`.
**Owner:** Engineering / ML Team

---

## 1. Problem Statement

Traditional fixed-parameter compression (e.g., JPEG q=75, H.264 CRF=23) applies the same settings to all media, resulting in:

- Over-compression of complex/high-detail content (visible artifacts).
- Under-compression of simple/low-detail content (wasted bytes).
- No automatic quality verification or retry.

We need a system that **reduces file size by 60-80% while maintaining acceptable perceptual quality**, using AI to select optimal parameters per file.

Target reference:
- Video: 50 MB → ~15 MB (~70% reduction)
- Image: 10 MB → ~2 MB (~80% reduction)

## 2. Objectives & Success Criteria

### 2.1 Objectives
1. Compress both **images** (JPEG, PNG, WebP, AVIF) and **videos** (MP4/H.264, H.265, VP9, AV1).
2. Use AI/ML to predict content characteristics and select optimal compression parameters.
3. Auto-evaluate output quality and iteratively adjust parameters if quality/size targets are missed.
4. Benchmark AI-adaptive vs. traditional fixed compression with reproducible reports.

### 2.2 Success Criteria (Must Meet)

| Metric | Image Target | Video Target |
|---|---|---|
| File-size reduction | ≥70% (e.g., 10 MB → ≤3 MB, stretch ≤2 MB) | ≥60% (e.g., 50 MB → ≤20 MB, stretch ≤15 MB) |
| Perceptual quality | SSIM ≥0.92, PSNR ≥32 dB, LPIPS ≤0.15 | SSIM ≥0.90, PSNR ≥32 dB, VMAF ≥85 |
| Processing overhead vs fixed | ≤2.5x time | ≤2.0x time (with fast preset) |
| Auto-retry success rate | ≥95% of files meet quality floor without manual intervention | Same |
| Comparison report | Required per run: size, quality, time, RD-curve | Required |

Failure condition: If SSIM <0.85 or VMAF <75, output is rejected and original is preserved + flag raised.

## 3. Scope

### In Scope
- Input: JPG, JPEG, PNG, WebP, BMP, TIFF → Output: JPEG / WebP / AVIF (configurable)
- Input: MP4, MOV, MKV, AVI, WebM → Output: MP4 (H.264/H.265) + WebM (VP9/AV1 optional)
- CLI + Python API + minimal Web UI (upload, compare slider, metrics dashboard)
- Batch folder processing
- AI parameter selector + quality evaluator + retry loop
- Evaluation harness + CSV/JSON/Markdown report generator

### Out of Scope (v1)
- Real-time streaming / live transcoding
- Audio-only optimization (passthrough / AAC 128k default)
- DRM content, 8K HDR10+ tone-mapping (passthrough only)
- Mobile SDK (future v2)

## 4. Users & Use Cases

1. **Developer / Researcher:** Run `compress --input ./media --ai` and get report comparing AI vs fixed.
2. **Content Platform:** Batch-compress UGC uploads to save storage/bandwidth.
3. **Evaluator:** View side-by-side original vs compressed + metrics to approve thresholds.

User stories:
- US1: As a user, I can drag-drop an image/video and get compressed output + size savings %.
- US2: As a user, I can see PSNR/SSIM/VMAF, processing time, and AI-chosen params.
- US3: As a user, I can toggle AI vs Fixed mode and see delta.
- US4: As a system, if quality < threshold, I auto-adjust params and re-encode (max N retries).

## 5. Functional Requirements

### FR1: Ingestion & Analysis
- FR1.1 Accept single file, directory, or URL. Validate codec, resolution, size, duration.
- FR1.2 Extract features: resolution, bitrate, entropy, texture energy (Laplacian variance), edge density, color histogram, faces/text detection flag, motion vectors / SI-TI for video, noise estimate.
- FR1.3 Classify content: `photo-natural / graphic-screen / textured / low-light-noisy / high-motion / talking-head / animation` with confidence score.

### FR2: AI Parameter Selection
- FR2.1 Image model outputs: `format, quality (5-95), subsampling (4:4:4/4:2:0), resize factor, denoise strength, effort/speed`.
- FR2.2 Video model outputs: `codec, CRF/CQ (18-35), preset (ultrafast..veryslow), resolution scale (1.0/0.75/0.5), fps cap, GOP, bitrate ceiling, denoise + deblock flags`.
- FR2.3 Heuristic fallback if model missing/low-confidence: rule table (e.g., high-texture → higher quality/lower CRF; graphic → PNG→WebP lossless/lossy mix).
- FR2.4 Support two AI modes:
  - `predict-once` (fast, single pass)
  - `optimize-search` (Bayesian / random search over k trials, pick best RD trade-off)

### FR3: Compression Engine
- FR3.1 Images: Pillow + pillow-avif + cwebp/cavif backends. Preserve EXIF optionally, strip by default.
- FR3.2 Videos: FFmpeg wrapper (ffmpeg-python). 2-pass optional for target-size mode. Hardware accel flag (NVENC/QSV) if available.
- FR3.3 Deterministic seeds, temp-file cleanup, preserve originals (never overwrite).

### FR4: Auto Evaluation & Adjustment Loop
- FR4.1 Compute after each encode:
  - Images: size ratio, PSNR, SSIM, MS-SSIM, LPIPS (optional), encode+eval time.
  - Videos: size ratio, PSNR, SSIM, VMAF (if model available), bitrate, fps, encode time.
- FR4.2 Decision logic:
  ```
  if quality < Q_min: increase quality (quality+10 / CRF-3) and retry (up to 3x)
  elif size_reduction < S_target and quality > Q_high_margin: decrease quality (quality-10 / CRF+2) and retry (up to 2x)
  else: accept
  ```
- FR4.3 Log every attempt: params, metrics, time to `runs/<timestamp>/attempts.json`.

### FR5: Comparison Mode
- FR5.1 Fixed baselines:
  - Image fixed: JPEG q=75, 4:2:0 (and WebP q=75 for fair pair).
  - Video fixed: H.264 CRF=23, preset=medium, no scaling.
- FR5.2 AI mode vs Fixed mode run on same inputs, same machine, output to side-by-side folders.
- FR5.3 Generate `comparison_report.{md,json,csv}` with: original size, fixed size, AI size, % savings, PSNR/SSIM/VMAF each, time each, winner, RD-curve PNG.

### FR6: Reporting & UI
- FR6.1 CLI prints table + saves report. API returns JSON.
- FR6.2 Web UI (Streamlit/Gradio or FastAPI+HTML): upload, before/after slider, metrics cards, param explanation ("AI chose CRF 27 because high-motion + low texture").
- FR6.3 Explainability: show content class, confidence, and SHAP/top-feature contributions (or rule trace).

## 6. Non-Functional Requirements

- NFR1: Python 3.10+, cross-platform (Win/Linux/Mac). FFmpeg bundled or auto-checked.
- NFR2: Processing time: image <5s (1080p), video <2x realtime on CPU medium preset (e.g., 30s 1080p <60s).
- NFR3: No data loss: original never mutated; all runs reproducible via `config.yaml + seed`.
- NFR4: Test coverage ≥70% for core pipeline; sample dataset (5 images + 3 videos) in `data/samples/`.
- NFR5: Logging structured; PII: strip GPS EXIF by default.

## 7. Proposed Architecture

```
                ┌──────────────────┐
Input →─────────│ Media Analyzer   │→ features.json (res, entropy, SI/TI, class)
                └────────┬─────────┘
                         ▼
                ┌──────────────────┐
                │ AI Param Selector│→ params.json (quality/CRF/preset/scale)
                │ - classifier     │
                │ - regressor / BO │
                └────────┬─────────┘
                         ▼
                ┌──────────────────┐     ┌──────────────┐
                │ Compressor       │→──→ │ Evaluator    │→ metrics.json
                │ Pillow / FFmpeg  │←─── │ PSNR/SSIM/   │ (retry if needed)
                └────────┬─────────┘  retry  │ VMAF/LPIPS │
                         ▼                   └──────────────┘
                ┌──────────────────┐
                │ Comparator +     │→ comparison_report.md/json/csv + RD plots
                │ Reporter         │
                └──────────────────┘
```

Suggested stack:
- Core: Python, Pillow, OpenCV, numpy, scikit-image (SSIM/PSNR), ffmpeg-python, PyTorch or scikit-learn for classifier/regressor.
- VMAF: `ffmpeg libvmaf` or Netflix VMAF binary (optional, fallback to SSIM if missing).
- LPIPS: `lpips` torch package (optional, CPU-friendly off by default).
- App: FastAPI + Streamlit (or Gradio for speed), Typer for CLI, Pydantic for configs.
- Exp tracking: MLflow or plain JSONL (keep simple for v1).

## 8. AI/ML Design (v1 Pragmatic)

Phase 1 (no training needed, ship fast):
- Hand-crafted feature extractor + rule-based + lightweight sklearn model trained on small labeled set (e.g., DIV2K + CLIC images, MCL-V clips).
- Bayesian optimization (`scikit-optimize`) for `optimize-search` mode: maximize `score = α*quality_norm + β*size_saving - γ*time_norm`.

Phase 2 (improvement):
- Train CNN (MobileNetV3) or ViT-tiny to predict optimal quality/CRF directly from thumbnail / clip preview.
- RL or learned RD model to skip full encodes.

Model artifacts: `models/image_classifier.pkl`, `models/param_regressor.pkl`, `models/README.md` with training data + accuracy.

Minimum viable AI: even a decision-tree on 6 features counts as "AI-assisted" if it beats fixed baseline on the report — document features + accuracy.

## 9. Metrics & Evaluation Protocol

1. Dataset: include `data/samples/` — natural photo, graphic/screenshot, portrait, noisy low-light, textured; video: high-motion sport, talking-head, animation.
2. Run both modes:
   ```bash
   python scripts/benchmark.py data/samples   # -> runs/bench_*/report.{md,csv,json}
   ```
3. Report columns: `file, orig_KB, fixed_KB, ai_KB, fixed_saving_%, ai_saving_%, fixed_psnr/ssim/vmaf, ai_psnr/ssim/vmaf, fixed_time_s, ai_time_s`.
4. Plots: RD-curve (bitrate vs SSIM/VMAF), bar chart savings vs quality.
5. Acceptance: AI must achieve ≥10pp better size saving at equal-or-better quality on average, OR equal saving at ≥+1dB PSNR / +0.02 SSIM.

Quality metric definitions:
- PSNR (dB, higher better), SSIM (0-1), VMAF (0-100), LPIPS (0-1, lower better), BPP / bitrate, encode time.

## 10. API / CLI Sketch

```bash
# Single image (AI, auto-retry) — real entrypoint
python -c "from src.pipeline import compress_auto; compress_auto('data/samples/photo.jpg','runs/out/photo.webp',mode='ai')"

# Batch video compare — real entrypoint
python scripts/benchmark.py data/samples   # -> runs/bench_*/report.{md,csv,json}

# Serve UI + API
python -m uvicorn backend.main:app --port 8000
```

```python
from src.pipeline import compress_auto
result = compress_auto("data/samples/clip.mp4", "runs/out/clip.mp4", mode="ai")
print(result) # {out, orig_size, new_size, attempts, best, total_ms, explanation, class}
```

Config `config.yaml` (live values):
```yaml
image: {formats: [webp, jpeg], min_ssim: 0.95, min_psnr: 33.0, target_saving: 0.70, max_retries: 3}
video: {codec: libx264, min_ssim: 0.92, min_psnr: 32.0, target_saving: 0.60, preset: veryfast, max_retries: 2}
ai: {mode: predict-once, explain: true}
```

## 11. Milestones (Suggested 4-Week Plan)

- **M1 (Wk1):** Analyzer + fixed compressor + evaluator (PSNR/SSIM) + CLI. Baseline report works.
- **M2 (Wk2):** Feature classifier + predict-once selector + retry loop + VMAF.
- **M3 (Wk3):** Benchmark harness + reports + RD plots + FastAPI/Streamlit UI.
- **M4 (Wk4):** Optimize-search (Bayesian), AVIF/AV1, model training doc, final comparison on full sample set.

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| VMAF binary missing / slow | Make optional; fallback to SSIM; document |
| AV1/H.265 slow on CPU | Default H.264 medium; H.265/AV1 behind flag + HW accel detection |
| AI worse than fixed on some files | Retry loop + quality floor guarantees no regression; report honestly |
| Large video OOM/timeout | Chunked encode, resolution cap, timeout + graceful fail |

## 13. Deliverables Checklist

- [ ] `src/` pipeline + `tests/` + `config.yaml`
- [ ] `models/` + training notebook/script
- [ ] `data/samples/` (or download script)
- [ ] `runs/<date>/comparison_report.md + .json + .csv + plots`
- [ ] `README.md` with install, usage, results table
- [ ] Demo screenshots / UI link

## 14. Open Questions

1. Target output formats locked to WebP/AVIF + H.264/H.265, or must support AV1 in v1?
2. VMAF required or SSIM-sufficient for grading?
3. Max acceptable encode time multiplier for AI-search mode?

---

## Appendix A: Measured Report (reproduced, not a target)

From `python scripts/benchmark.py data/samples`, 2026-09-21 (`runs/bench_20260921_232532/report.md`):

| File | Orig | Fixed | AI | Saving (F/AI) | SSIM (F/AI) | PSNR (F/AI) | Time (F/AI) |
|---|---|---|---|---|---|---|---|
| photo.jpg | 21177 B | 6030 B | 1632 B | 71.5% / 92.3% | 0.9999 / 0.9999 | 50.93 / 49.85 | 66ms / 217ms |
| graphic.png | 1621 B | 3662 B | 924 B | -125.9% / 43.0% | 1.0 / 1.0 | 51.33 / 52.15 | 151ms / 254ms |
| clip.mp4 | 48275 B | 28197 B | 25807 B | 41.6% / 46.5% | 0.9999 / 0.9999 | 49.59 / 45.28 | 5340ms / 4419ms |

> Re-run `scripts/benchmark.py` to regenerate. Do not hardcode other numbers.
