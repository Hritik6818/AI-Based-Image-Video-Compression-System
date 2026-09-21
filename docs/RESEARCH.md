# Research: Are Good Solutions Available? How Good?

## Learned image compression (LIC)
- **Ballé hyperprior / Minnen joint AR-hierarchical, ELIC, MLIC/MLICv2, WeConvene (DWT+LIC), CMIC (content-adaptive Mamba), GNN-GLIC (CVPR 2026)**: all beat VVC-Intra on Kodak/Tecnick/CLIC by ~8–24% BD-rate (PSNR/MS-SSIM). Verdict: SOTA quality, but heavy (GPU, slow, complex) — overkill for this project's ms/CPU goal.
- **JPEG AI (ISO/IEC)**: emerging standard, CNN transform + entropy coding; good RD but not yet broadly deployed.
- **Practical takeaway**: for CPU + ms latency, classical **WebP/JPEG with content-adaptive quality** (what v1 builds) beats fixed JPEG with ~100× less complexity than LIC nets. Upgrade path: plug a tiny MobileNet quality-predictor later.

## Neural video compression (NVC)
- **DVC (first E2E), DCVC family (DCVC-TCM/HEM/DC/DCVC-FM), DCVC-RT (CVPR 2025: 125fps 1080p, −21% vs VVC)**: now match/beat H.265 and near H.266 (VVC) on PSNR/MS-SSIM; ECM still competitive. Verdict: excellent RD, but needs GPU + custom decoders — not browser-playable MP4.
- **Traditional**: H.264 (universal), H.265 −40% vs H.264, AV1 −20–30% vs H.265 but slow, VVC best RD but 27–174× slower encode than AV1.
- **Practical takeaway**: H.264 CRF-adaptive (our v1) is the right latency/compatibility trade; add H.265/AV1 behind a flag; track DCVC-RT for v2 GPU mode. VMAF (not just PSNR) must guide video — our report flags this as TODO.

## Quality metrics
- PSNR (signal), SSIM/MS-SSIM (structure, closest to "95% info"), VMAF (Netflix, video perceptual gold), LPIPS (deep perceptual). Our stack: PSNR+SSIM now (numpy, ms), VMAF/LPIPS optional next.
- Caution (Nov 2025 study): metrics tuned on traditional codecs can overestimate neural codecs — always keep human side-by-side check (our UI does).

Bottom line: SOTA research is real and strong, but **adaptive-classical + auto-eval is the best effort/quality/latency trade for v1**; go neural only with GPU budget.
