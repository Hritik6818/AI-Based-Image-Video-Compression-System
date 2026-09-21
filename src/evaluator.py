"""Minimal SSIM/PSNR with numpy only (no scikit-image needed)."""
import numpy as np
from PIL import Image

def load_gray(p, max_side=512):
    im = Image.open(p).convert("L")
    im.thumbnail((max_side, max_side))
    return np.asarray(im, dtype=np.float64)

def psnr(a: np.ndarray, b: np.ndarray, peak=255.0) -> float:
    mse = float(np.mean((a - b) ** 2))
    if mse == 0:
        return 100.0
    import math
    return 20 * math.log10(peak / math.sqrt(mse))

def ssim(a: np.ndarray, b: np.ndarray) -> float:
    # Simplified global SSIM (Wang et al.) — fast, ms latency.
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu1, mu2 = a.mean(), b.mean()
    s1, s2 = a.var(), b.var()
    s12 = float(np.mean((a - mu1) * (b - mu2)))
    num = (2 * mu1 * mu2 + C1) * (2 * s12 + C2)
    den = (mu1**2 + mu2**2 + C1) * (s1 + s2 + C2)
    return float(num / den) if den else 1.0

def image_metrics(orig_path, comp_path):
    a = load_gray(orig_path)
    b = load_gray(comp_path)
    # resize b to a's shape for comparison
    if a.shape != b.shape:
        b = np.asarray(Image.fromarray(b.astype("uint8")).resize(a.shape[::-1]), dtype=np.float64)
    return {"psnr": round(psnr(a, b), 2), "ssim": round(max(0.0, min(1.0, ssim(a, b))), 4)}


def _extract_frame(video_path, out_jpg, ss=1.0):
    import subprocess
    import os
    os.makedirs(os.path.dirname(out_jpg) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ss),
                    "-i", video_path, "-frames:v", "1", out_jpg],
                   check=True)
    return out_jpg


def video_metrics(orig_path, comp_path, samples=(0.5, 1.5, 2.5)):
    """Real quality estimate: compare identical-timestamp frames. No hardcoded values."""
    import tempfile
    psnrs, ssims = [], []
    with tempfile.TemporaryDirectory() as td:
        for i, t in enumerate(samples):
            fo = f"{td}/o{i}.jpg"
            fc = f"{td}/c{i}.jpg"
            try:
                _extract_frame(orig_path, fo, ss=t)
                _extract_frame(comp_path, fc, ss=t)
            except Exception:
                continue  # timestamp beyond short clip; try next sample
            a = load_gray(fo)
            b = load_gray(fc)
            if a.shape != b.shape:
                b = np.asarray(Image.fromarray(b.astype("uint8")).resize(a.shape[::-1]),
                               dtype=np.float64)
            psnrs.append(psnr(a, b))
            ssims.append(max(0.0, min(1.0, ssim(a, b))))
    if not ssims:
        raise RuntimeError(f"could not extract comparable frames from {orig_path} / {comp_path}")
    return {"psnr": round(sum(psnrs) / len(psnrs), 2),
            "ssim": round(sum(ssims) / len(ssims), 4)}
