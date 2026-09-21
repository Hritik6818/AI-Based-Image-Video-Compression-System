# HOW TO USE

## Local run (5 min)
```powershell
pip install -r requirements.txt
python scripts/make_samples.py        # creates data/samples demo images + video
python scripts/benchmark.py data/samples   # -> runs/bench_*/report.md
python -m uvicorn backend.main:app --port 8000
# open http://localhost:8000
```
Upload image/video → pick AI vs Fixed → see score/10, SSIM, saving%, download.

## API
```powershell
curl -F "file=@data/samples/photo.jpg" -F "mode=ai" http://localhost:8000/api/compress
curl http://localhost:8000/api/jobs?limit=5
```

## DB
sqlite at `db/jobs.db`, table `jobs(...)`. View: `sqlite3 db/jobs.db "select id,filename,score_10,verdict from jobs;"`
Render: set `DB_PATH=/var/data/jobs.db` with a persistent disk, or switch to Postgres (see DEPLOY_RENDER.md).
