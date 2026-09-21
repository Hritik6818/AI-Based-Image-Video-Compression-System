import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import compress_auto
r = compress_auto("data/samples/photo.jpg", "runs/out/smoke.webp", mode="ai")
b = r["best"]
print({k: r[k] for k in ("orig_size", "new_size", "total_ms", "class")})
print(b["metrics"], b["score"])
assert b["metrics"]["ssim"] >= 0.85, "quality floor failed"
print("SMOKE OK")
