"""Build docs/AI-Image-Video-Compressor-Guide.pdf (basic -> advanced + interview)."""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, ListFlowable, ListItem)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "AI-Image-Video-Compressor-Guide.pdf")

ss = getSampleStyleSheet()
TITLE = ParagraphStyle("Title2", parent=ss["Title"], fontSize=22, leading=26, spaceAfter=4)
SUB = ParagraphStyle("Sub", parent=ss["Normal"], fontSize=11, leading=15, textColor=colors.HexColor("#444444"))
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, leading=20, spaceBefore=14, spaceAfter=6,
                    textColor=colors.HexColor("#1a3a5c"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=4,
                    textColor=colors.HexColor("#2a5a8c"))
B = ParagraphStyle("B", parent=ss["Normal"], fontSize=9.5, leading=13.5, spaceAfter=4)
BI = ParagraphStyle("BI", parent=B, leftIndent=12, bulletIndent=4, spaceAfter=2)
CODE = ParagraphStyle("CODE", parent=ss["Code"], fontSize=8.2, leading=11, backColor=colors.HexColor("#f2f4f7"),
                      borderPadding=4, spaceAfter=6)
CELL = ParagraphStyle("CELL", parent=ss["Normal"], fontSize=8.4, leading=11)
CHEAD = ParagraphStyle("CHEAD", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")

story = []


def t(text):
    story.append(Paragraph(text, TITLE))


def sub(text):
    story.append(Paragraph(text, SUB))


def h1(text):
    story.append(Paragraph(text, H1))


def h2(text):
    story.append(Paragraph(text, H2))


def p(text):
    story.append(Paragraph(text, B))


def bullets(items):
    story.append(ListFlowable([ListItem(Paragraph(i, B), leftIndent=14) for i in items],
                              bulletType="bullet", leftIndent=10))


def code(text):
    for line in text.strip().split("\n"):
        story.append(Paragraph(line.replace(" ", "&nbsp;"), CODE))


def table(headers, rows):
    data = [[Paragraph(h, CHEAD) for h in headers]] + [[Paragraph(c, CELL) for c in r] for r in rows]
    w = (A4[0] - 36 * mm) / len(headers)
    tbl = Table(data, colWidths=[w] * len(headers), repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fb")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))


# ---------------- COVER ----------------
story.append(Spacer(1, 40))
t("AI Image &amp; Video Compressor")
sub("Complete Guide: Basic to Advanced - How It Works, The Maths, AI-Adaptive vs Fixed Baseline, Interview Preparation &amp; Edge Cases")
story.append(Spacer(1, 8))
p("Covers the actual codebase: analyzer, selector, compressor, evaluator, scoring, pipeline, FastAPI backend, static frontend, benchmark harness. "
  "Everything is honest about what is implemented vs what is roadmap.")
story.append(Spacer(1, 4))
p("Stack: Python, Pillow, numpy, ffmpeg (H.264), FastAPI. Metrics: PSNR, SSIM, 1-10 composite score. DB: sqlite jobs log.")
PageBreak()

# ---------------- 1. BIG PICTURE ----------------
h1("1. Big Picture (30-Second Version)")
p("Upload an image or video. The backend decides image vs video by file extension. In AI mode the file is analyzed, "
  "classified into a content class, and given custom compression settings. It is compressed, then real quality (PSNR/SSIM) "
  "is measured. If quality or size targets are missed, settings are auto-adjusted and it re-encodes (up to 4 attempts). "
  "Every result is scored 1-10 against a fixed baseline (JPEG q75 / H.264 CRF23) so the AI must prove it wins.")
code("browser -> POST /api/compress -> compress_auto() -> analyze -> predict\n"
     "-> compress -> evaluate -> retry? -> score -> sqlite log -> download URL")

# ---------------- 2. IMAGE BASICS ----------------
h1("2. Images: Basics to Maths")
h2("2.1 What an image is")
p("A digital image is a grid of pixels. Each pixel in RGB is 3 numbers (Red, Green, Blue), 0-255 each. "
  "A 1600x1200 photo = 1.92M pixels x 3 bytes = ~5.5 MB raw. Compression removes redundancy so we store far less.")
h2("2.2 Why images compress: three redundancies")
bullets([
    "<b>Spatial:</b> neighbours look alike (blue sky). Predict a pixel from neighbours, store only the difference.",
    "<b>Perceptual:</b> eyes notice brightness detail more than colour detail - so JPEG stores colour at half resolution (chroma subsampling 4:2:0).",
    "<b>Statistical:</b> common patterns get short codes (Huffman / entropy coding).",
])
h2("2.3 JPEG maths (the fixed baseline)")
p("Steps: (1) RGB to YCbCr, downsample Cb/Cr. (2) Split into 8x8 blocks. (3) DCT - converts each block into 64 frequencies "
  "(like a prism splitting light). (4) Quantization - divide high frequencies by large numbers and round: this is the LOSSY step, "
  "controlled by the quality parameter q. (5) Zigzag + run-length + Huffman coding (lossless). Lower q = coarser rounding = smaller file, more block artifacts.")
h2("2.4 WebP maths (the AI default)")
p("WebP lossy reuses VP8 video intra-frame coding: predict each block from already-decoded neighbours (many directional modes), "
  "store only the residual, transform + quantize it, entropy-code with LZ77 + Huffman. Better prediction than JPEG's DCT-only "
  "approach is why WebP is typically 25-35% smaller than JPEG at equal quality. The quality parameter plays the same role: quantizer step size.")
h2("2.5 PSNR and SSIM (how we judge, with formulas)")
p("MSE = mean of squared pixel differences. PSNR = 20 x log10(255 / sqrt(MSE)), in dB. +6 dB means roughly 4x less error; "
  "our floor ~32-33 dB. PSNR is pure signal math - blind to perception.")
p("SSIM compares luminance, contrast and structure in windows: SSIM = l x c x s, each 0-1, using local means, variances and "
  "covariance with stabilizers C1=(0.01x255)^2, C2=(0.03x255)^2 (see src/evaluator.py:ssim). "
  "SSIM 0.95 ~= '95% information retained' - our headline target. SSIM 1.0 = identical.")
h2("2.6 Our image pipeline (code mapping)")
table(["Stage", "File:function", "What happens"],
      [["Analyze", "analyzer.py:features()", "256px gray copy: Laplacian-variance texture, gradient edge density, colorfulness, 32-bin luminance entropy, megapixels"],
       ["Classify", "analyzer.py:classify()", "graphic-screen / smooth-lowdetail / textured / photo-natural + confidence"],
       ["Predict", "selector.py:predict_image_params()", "class -> WebP quality 70-85; scale 0.85 if >4MP, 0.75 if >12MP"],
       ["Compress", "compressor.py:compress_image()", "Pillow save with quality/scale"],
       ["Evaluate", "evaluator.py:image_metrics()", "real PSNR + SSIM on <=512px gray copies"],
       ["Retry", "pipeline.py loop + selector.adjust_on_quality()", "ssim<min -> quality+8; saving low with headroom -> quality-8; max 4 tries"]])

# ---------------- 3. VIDEO ----------------
h1("3. Video: Capture to Compressed File")
h2("3.1 What video is")
p("Video = 25-60 still images (frames) per second + usually an audio track, inside a container (MP4). Raw 1080p30 = "
  "1920x1080x3 bytes x30 = ~187 MB/s. Compression exploits a 4th redundancy on top of image ones:")
bullets([
    "<b>Temporal redundancy:</b> consecutive frames are nearly identical. Store one full frame, then only what changed.",
    "<b>I-frame (keyframe):</b> full image, like JPEG. <b>P-frame:</b> 'take previous frame, move these blocks here (motion vectors), add this small correction'. Skipped blocks cost ~nothing.",
    "<b>Motion estimation:</b> encoder searches previous frame for matching 16x16/8x8 blocks - the most expensive step (this is why presets matter).",
    "<b>GOP:</b> group of pictures between I-frames (e.g. 250 frames). More P-frames = smaller, but seeking/errors need the next I-frame.",
])
h2("3.2 H.264 encode pipeline (what ffmpeg does for us)")
code("frames -> motion estimation (vectors) -> residual = frame - prediction\n"
     "-> 4x4/8x8 integer transform -> quantization (CRF controls step)\n"
     "-> entropy coding (CABAC) -> MP4  |  audio -> AAC 128k")
p("CRF (Constant Rate Factor, 0-51, we use 18-33) sets quality: +2 CRF ~= 25% fewer bits at slightly lower quality. "
  "Preset (ultrafast..veryslow) trades encode time for compression efficiency at the same CRF: slower = smarter motion search. "
  "Decode is the exact inverse: parse -> dequantize -> inverse transform -> add motion prediction -> display. Decoding is cheap; encoding is expensive.")
h2("3.3 Our video pipeline (code mapping)")
bullets([
    "Classify from a <b>real extracted frame</b> at t=1s (_video_thumbnail_features) - never fabricated numbers.",
    "Map class to CRF 20-28, preset veryfast, optional downscale (selector.py:predict_video_params).",
    "Encode: ffmpeg libx264 + AAC (compressor.py:compress_video).",
    "Measure <b>real</b> quality: extract frames at t=0.5/1.5/2.5s from source AND output, compare PSNR/SSIM (evaluator.py:video_metrics).",
    "Retry: CRF-3 if quality low, CRF+2 if saving low with headroom.",
])
p("Honest limit: frame-sample SSIM is a proxy, not full VMAF. VMAF-guided quality is roadmap (see RESEARCH.md).")

# ---------------- 4. AI VS FIXED ----------------
h1("4. AI-Adaptive vs Fixed Baseline")
p("Purpose of fixed: a frozen reference (image JPEG q75; video H.264 CRF23 preset medium, single pass, never retried) so the AI "
  "must prove itself on identical inputs. Purpose of AI: different content needs different settings - smooth graphics compress "
  "far more than noisy texture at the same perceived quality, so one setting for all files wastes bytes or damages detail.")
table(["Aspect", "Fixed baseline", "AI-adaptive"],
      [["Decided in", "pipeline.py else-branch (params hardcoded)", "analyzer + selector (params predicted per file)"],
       ["Attempts", "exactly 1 (rounds=1)", "up to 4 (max_retries+1) with measured retry"],
       ["Quality check", "none - output accepted blind", "real PSNR/SSIM every attempt, floor min_ssim"],
       ["Measured photo.jpg", "7233 B, SSIM 0.9999, 9.14/10", "1632 B, SSIM 0.9999, 9.79/10"],
       ["Measured graphic.png", "4188 B - BIGGER than input (-158%)", "924 B (WebP switch), 8.56/10"],
       ["Measured clip.mp4", "36834 B, 8.07/10", "25807 B, 8.65/10"]])
p("Read the wart honestly in interviews: fixed JPEG inflating a tiny PNG proves the point - blind settings fail on some content, adaptation wins.")

# ---------------- 5. HOW MUCH AI/ML ----------------
h1("5. How Much AI / ML / Deep Learning / CNN Is Used?")
p("Honest accounting - say exactly this in interviews:")
table(["Technique", "Used?", "Where / notes"],
      [["Hand-crafted features + statistics", "YES (core)", "texture/edge/color/entropy in analyzer.py"],
       ["Rule-based classifier (heuristic policy)", "YES (core)", "classify() thresholds; the 'AI brain' of v1"],
       ["Closed-loop control (measure -> adjust -> retry)", "YES (core)", "pipeline retry loop; the intelligence that guarantees floors"],
       ["Classical ML (sklearn trees/SVM)", "NO", "upgrade path: train classifier on labeled DIV2K/CLIC crops"],
       ["CNN / deep learning at runtime", "NO", "0% - no neural net runs in v1; deliberate CPU/ms-latency choice"],
       ["Learned codecs (ELIC/MLIC, DCVC, JPEG-AI)", "NO (surveyed)", "docs/RESEARCH.md: beat VVC ~8-24% BD-rate but need GPU + custom decoders"],
       ["Bayesian optimization", "NO (roadmap)", "search quality/CRF space instead of fixed +-steps"]])
p("Defensible line: v1 is an adaptive decision system with measured feedback that beats the baseline on every sample - "
  "ML in the 'learning from data to make decisions' sense, with a documented path to learned models. Never claim a CNN runs in v1.")

# ---------------- 6. SCORING ----------------
h1("6. Scoring Maths (src/scoring.py)")
p("score = 4.0xSSIM + 2.5xPSNRnorm + 2.5xsaving + 1.0xspeed, clipped 0-10. PSNRnorm=(PSNR-20)/20. "
  "Speed = 1/(1+t/10) images, 1/(1+t/120) video. Verdicts: SSIM>=0.95 & saving>=60% = ACCEPT (excellent); "
  ">=0.90 & >=50% = ACCEPT (good); >=0.85 = MARGINAL; else REJECT; unevaluable quality = NEEDS-REVIEW. Acceptance bar 7.0.")

# ---------------- 7. INTERVIEW Q&A ----------------
h1("7. Interview Q&A Bank")
table(["Question", "Answer (30-45s)"],
      [["Walk me through a request", "Browser POSTs file+mode; main.py saves it, picks webp/mp4 by extension, calls compress_auto; pipeline analyzes, classifies, predicts, encodes, measures, retries; result logged to sqlite, JSON + download URL returned."],
       ["Why not just fixed q75?", "One setting misfires per content: our fixed JPEG inflated a PNG by 158%. Adaptation picks per-file settings and verifies."],
       ["Why WebP default?", "~25-35% smaller than JPEG at equal quality via better VP8 intra prediction; JPEG kept as fixed baseline + fallback."],
       ["CRF vs bitrate?", "CRF=constant quality, bitrate varies with content; +2 CRF ~= -25% bits. We control quality, not size."],
       ["Preset effect?", "Same CRF, slower preset = smarter motion search = fewer bits. We use veryfast (latency) vs medium (baseline)."],
       ["Why is video seconds not ms?", "Encode searches motion across millions of blocks per frame - inherently seconds; ms claims would exclude the encode."],
       ["Where is the AI?", "Heuristic policy + feedback loop; no runtime neural net. Beats fixed on all samples; CNN/BO is roadmap with research surveyed."],
       ["Failure handling?", "Quality floor rejects bad output; exceptions propagate (no fake metrics); NEEDS-REVIEW when unevaluable; originals never overwritten."],
       ["PNG transparency?", "Known limitation: converted to RGB, alpha dropped. Say it before they ask; fix = keep alpha via WebP lossless/palette path."],
       ["Scale the system?", "Stateless FastAPI + ffmpeg workers, job queue (Celery/Redis), object storage, Postgres; GPU nodes for neural codecs later."]])

# ---------------- 8. EDGE CASES ----------------
h1("8. Edge Cases & How Code Handles Them")
table(["Edge case", "Behaviour"],
      [["Tiny file (adds header overhead)", "Reported honestly - even negative saving; verdict MARGINAL; never hidden"],
       ["PNG with transparency", "Alpha dropped (RGB convert) - documented limitation"],
       ["Corrupt/unsupported file", "PIL/ffmpeg raises; API returns error, nothing fabricated"],
       ["Huge image (>12MP)", "auto downscale 0.75 (0.85 if >4MP) before encode"],
       ["Short video (< sample timestamps)", "skipped timestamps continue to next sample; total failure raises honestly"],
       ["Silent video / no audio", "AAC flags harmless; ffmpeg maps if present"],
       ["Fixed beats AI on some file", "possible - report shows both; retry floor guarantees no quality regression"],
       ["Concurrent uploads", "uuid filenames prevent collision; sqlite serializes logs"],
       ["Stale UI after update", "hard refresh (JS cached, seen as HTTP 304)"]])

h1("9. File Map (36 files)")
p("Core: src/pipeline.py, selector.py, evaluator.py, analyzer.py, backend/main.py, src/scoring.py. "
  "Support: src/compressor.py, src/db.py, frontend/app.js. Evidence: scripts/benchmark.py, tests/test_pipeline.py. "
  "Docs: README, PRD, docs/*. Scaffolding (lowest priority): src/__init__.py, runs/.gitkeep, .gitignore, scripts/init_repo.ps1.")

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                        leftMargin=18 * mm, rightMargin=18 * mm,
                        title="AI Image & Video Compressor - Complete Guide",
                        author="Project Guide")
doc.build(story)
print("wrote", OUT)
