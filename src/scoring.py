"""1-10 benchmark score. Tried methods: fixed q75 / CRF23 vs AI-adaptive; score picks winner."""
# score = 4.0*ssim01 + 2.5*psnr01 + 2.5*saving + 1.0*speed  (all 0..1 -> 1..10)
# ssim01 = ssim (already 0..1); psnr01 = clip((psnr-20)/20); saving = bytes saved ratio;
# speed01 = 1/(1+time_s/10) for images, 1/(1+time_s/120) for video.

def _clip(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def score(ssim, psnr, orig_b, new_b, time_s, kind="image"):
    saving = _clip(1 - new_b / max(1, orig_b))
    denom = 10 if kind == "image" else 120
    speed = 1 / (1 + time_s / denom)
    if ssim is None or psnr is None:
        # quality unevaluable: score only what was measured, flag for review
        raw = 2.5 * saving + 1.0 * speed
        sc = round(_clip(raw / 10, 0.02, 1.0) * 10, 2)
        return {"score_10": sc, "verdict": "NEEDS-REVIEW (quality unevaluable)",
                "parts": {"ssim": None, "psnr": None,
                          "saving": round(saving, 3), "speed": round(speed, 3)}}
    ssim01 = _clip(ssim)
    psnr01 = _clip((psnr - 20) / 20.0)
    raw = 4.0 * ssim01 + 2.5 * psnr01 + 2.5 * saving + 1.0 * speed  # 0..10
    sc = round(_clip(raw / 10, 0.02, 1.0) * 10, 2)
    if ssim >= 0.95 and saving >= 0.6:
        verdict = "ACCEPT (excellent)"
    elif ssim >= 0.90 and saving >= 0.5:
        verdict = "ACCEPT (good)"
    elif ssim >= 0.85:
        verdict = "MARGINAL"
    else:
        verdict = "REJECT"
    return {"score_10": sc, "verdict": verdict,
            "parts": {"ssim": round(ssim01, 3), "psnr": round(psnr01, 3),
                      "saving": round(saving, 3), "speed": round(speed, 3)}}
