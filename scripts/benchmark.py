"""Benchmark: AI vs fixed on a folder. Outputs runs/<ts>/report.{json,md,csv}."""
import os
import sys
import glob
import json
import csv
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import compress_auto

def run(indir, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = [f for f in glob.glob(os.path.join(indir, "*")) if os.path.isfile(f)]
    rows = []
    for src in files:
        name = os.path.basename(src)
        for mode in ("fixed", "ai"):
            dst = os.path.join(outdir, f"{mode}_{os.path.splitext(name)[0]}" +
                               (".webp" if src.lower().endswith((".jpg",".jpeg",".png",".webp",".bmp")) else ".mp4"))
            try:
                r = compress_auto(src, dst, mode=mode)
                b = r["best"]
                rows.append({"file": name, "mode": mode, "orig": r["orig_size"],
                             "new": r["new_size"],
                             "saving_pct": round(100*(1-r["new_size"]/r["orig_size"]),1),
                             "psnr": b["metrics"]["psnr"], "ssim": b["metrics"]["ssim"],
                             "score": b["score"]["score_10"], "verdict": b["score"]["verdict"],
                             "ms": r["total_ms"], "params": str(b["params"])})
            except Exception as e:
                rows.append({"file": name, "mode": mode, "error": str(e)})
    # write artifacts
    json.dump(rows, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    with open(os.path.join(outdir, "report.csv"), "w", newline="") as f:
        keys = sorted({k for r in rows for k in r})
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    with open(os.path.join(outdir, "report.md"), "w") as f:
        f.write("# Benchmark: AI vs Fixed\n\n|file|mode|orig|new|saving%|psnr|ssim|score/10|verdict|ms|\n|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"|{r.get('file')}|{r.get('mode')}|{r.get('orig')}|{r.get('new')}|{r.get('saving_pct')}|{r.get('psnr')}|{r.get('ssim')}|{r.get('score')}|{r.get('verdict')}|{r.get('ms')}|\n")
    print(f"Wrote {len(rows)} rows to {outdir}/report.md")
    return rows

if __name__ == "__main__":
    indir = sys.argv[1] if len(sys.argv) > 1 else "data/samples"
    ts = time.strftime("%Y%m%d_%H%M%S")
    run(indir, f"runs/bench_{ts}")
