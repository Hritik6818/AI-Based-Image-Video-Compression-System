"""FastAPI backend: upload -> AI compress -> score -> sqlite log."""
import os, time, shutil, uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.pipeline import compress_auto
from src.db import log_job, get_db

app = FastAPI(title="AI Compression API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UP, OUT = "uploads", "runs/out"
os.makedirs(UP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
DB = os.environ.get("DB_PATH", "db/jobs.db")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/compress")
async def compress(file: UploadFile = File(...), mode: str = Form("ai"),
                   min_ssim: float = Form(0.95)):
    fid = f"{uuid.uuid4().hex}_{file.filename}"
    src = os.path.join(UP, fid)
    with open(src, "wb") as f:
        shutil.copyfileobj(file.file, f)
    ext = os.path.splitext(file.filename)[1].lower()
    is_img = ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    dst = os.path.join(OUT, os.path.splitext(fid)[0] + (".webp" if is_img else ".mp4"))
    r = compress_auto(src, dst, mode=mode, min_ssim=min_ssim,
                      kind="image" if is_img else "video")
    b = r["best"]
    row = {"filename": file.filename, "kind": "image" if is_img else "video",
           "method": mode, "orig_size": r["orig_size"], "new_size": r["new_size"],
           "saving_pct": round(100 * (1 - r["new_size"] / max(1, r["orig_size"])), 1),
           "psnr": b["metrics"]["psnr"], "ssim": b["metrics"]["ssim"],
           "score_10": b["score"]["score_10"], "verdict": b["score"]["verdict"],
           "time_ms": r["total_ms"], "params": str(b["params"]),
           "created_at": int(time.time())}
    jid = log_job(DB, row)
    return {"job_id": jid, "download": f"/runs/out/{os.path.basename(dst)}", **r, **row}

@app.get("/api/jobs")
def jobs(limit: int = 20):
    con = get_db(DB)
    rows = con.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    cols = [d[0] for d in con.execute("SELECT * FROM jobs LIMIT 0").description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]

app.mount("/runs/out", StaticFiles(directory=OUT), name="out")
app.mount("/", StaticFiles(directory="frontend", html=True), name="ui")
