# Benchmark Scale 1–10

`score = 4.0·SSIM + 2.5·PSNR01 + 2.5·Saving + 1.0·Speed`, scaled 0–10.
- SSIM: raw 0–1. PSNR01 = clip((PSNR−20)/20). Saving = 1 − new/orig. Speed = 1/(1+t/10) image, 1/(1+t/120) video.
- Verdicts: ≥0.95 SSIM & ≥60% saving → ACCEPT (excellent); ≥0.90 & ≥50% → ACCEPT (good); ≥0.85 → MARGINAL; else REJECT.
- Acceptance: **score ≥ 7.0**. Compare AI vs fixed on same files; winner = higher score at equal-or-better SSIM.

Run: `python scripts/benchmark.py data/samples` → `runs/bench_*/report.{md,csv,json}`.
Report columns: file, mode, orig, new, saving%, psnr, ssim, score, verdict, ms, params.
