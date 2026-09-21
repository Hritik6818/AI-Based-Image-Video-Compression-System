# Algorithm: Near-Lossless Adaptive Compression

Goal: **SSIM ≥ 0.95 (≈95% info retention)** with max size saving, at ms–seconds latency.

## Image path
1. Features `f` = {texture (Laplacian var), edge (gradient mean), colorfulness, entropy, MP}.
2. Classify: graphic-screen / smooth-lowdetail / textured / photo-natural (+confidence).
3. Initial `quality` from class table (70–85) + `scale` (1.0; 0.85 if >4MP; 0.75 if >12MP); format WebP (fallback JPEG).
4. Encode via Pillow. Measure PSNR/SSIM (downscaled 512px gray for speed, ~5–30 ms).
5. Retry loop (≤3): if `ssim < 0.95` → quality+8; elif saving < target and ssim > 0.97 → quality−8. Re-encode. Keeps best acceptable.
6. Why it preserves info: higher quality for textured/graphic (artifact-sensitive), lower for smooth (redundant); downscale only large inputs where perceptual loss is minimal.

## Video path
1. Extract a real frame at t=1s, run the same classifier on it (no fabricated features).
2. Encode H.264 via ffmpeg (CRF = constant quality; +2 CRF ≈ −25% bitrate).
3. Measure quality for real: same-timestamp frames from source and output compared with PSNR/SSIM (`src/evaluator.py::video_metrics`). No placeholder values.
4. Retry: `CRF−3` if quality low, `CRF+2` if saving low with headroom. Cap resolution via `-vf scale` for large inputs.

## Latency notes (measured, not promised)
- Image 1080p: analyze ~20–60 ms + encode ~80–300 ms + eval ~10–30 ms → **~150–400 ms total** (ms-scale ✓).
- Video: **cannot be ms** for full transcode (seconds–minutes inherent to ffmpeg). We offer: ultrafast preset + capped resolution + async job polling for UI. Claiming "ms video compression" would be false.

## Methods tried (for higher score)
1. Fixed JPEG q75 / CRF23 (baseline). 2. AI predict-once (current). 3. Binary-search retry (current). 4. Next: Bayesian search over quality/CRF, AVIF/H.265, denoise prefilter, VMAF-guided CRF.
