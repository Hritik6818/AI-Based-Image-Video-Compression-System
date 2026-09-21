"""Auto pipeline: analyze -> predict -> compress -> evaluate -> retry. Latency measured in ms."""
import os
import tempfile
import time

from . import analyzer
from . import compressor
from . import evaluator
from . import scoring
from . import selector

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def _size(p):
    return os.path.getsize(p)


def _video_thumbnail_features(src):
    """Extract one real frame and analyze it. Raises instead of fabricating on failure."""
    with tempfile.TemporaryDirectory() as td:
        thumb = os.path.join(td, "thumb.jpg")
        evaluator._extract_frame(src, thumb, ss=1.0)
        feat = analyzer.features(thumb)
    cls, conf = analyzer.classify(feat)
    return feat, cls, conf


def compress_auto(src, out_path, mode="ai", min_ssim=0.95, target_saving=0.7,
                  max_retries=3, kind=None):
    t0 = time.perf_counter()
    ext = os.path.splitext(src)[1].lower()
    is_image = (kind == "image") or (ext in IMG_EXT)

    if is_image and mode == "ai":
        feat = analyzer.features(src)
        cls, conf = analyzer.classify(feat)
        params = selector.predict_image_params(cls, feat["mp"])
    elif not is_image and mode == "ai":
        feat, cls, conf = _video_thumbnail_features(src)
        params = selector.predict_video_params(cls)
    else:
        feat, cls, conf = {}, "fixed-baseline", 1.0
        if is_image:
            params = {"quality": 75, "format": "jpeg", "scale": 1.0}
        else:
            params = {"codec": "libx264", "crf": 23, "preset": "medium", "scale": 1.0}

    attempts = []
    rounds = 1 if mode == "fixed" else max_retries + 1  # fixed baseline: single pass, no retry
    with tempfile.TemporaryDirectory() as td:
        for i in range(rounds):
            last = (i == rounds - 1)
            tmp = out_path if last else os.path.join(
                td, f"try{i}{os.path.splitext(out_path)[1]}")
            it = time.perf_counter()
            if is_image:
                compressor.compress_image(src, tmp, quality=params.get("quality", 78),
                                          img_format=params.get("format", "webp"),
                                          scale=params.get("scale", 1.0))
                m = evaluator.image_metrics(src, tmp)
            else:
                compressor.compress_video(src, tmp, crf=params.get("crf", 25),
                                          preset=params.get("preset", "veryfast"),
                                          scale=params.get("scale", 1.0))
                m = evaluator.video_metrics(src, tmp)
            dt = time.perf_counter() - it
            s = scoring.score(m["ssim"], m["psnr"], _size(src), _size(tmp), dt,
                              kind="image" if is_image else "video")
            attempts.append({"try": i, "params": dict(params), "metrics": m,
                             "score": s, "time_ms": int(dt * 1000),
                             "size": _size(tmp)})
            low_q = m["ssim"] < min_ssim
            small_save = ((1 - _size(tmp) / _size(src)) < target_saving
                          and m["ssim"] > min_ssim + 0.02)
            if last or (not low_q and not small_save):
                if not last:
                    # accepted early: materialize the accepted tmp at out_path
                    compressor.compress_image(src, out_path,
                                              quality=params.get("quality", 78),
                                              img_format=params.get("format", "webp"),
                                              scale=params.get("scale", 1.0)) if is_image else \
                        compressor.compress_video(src, out_path, crf=params.get("crf", 25),
                                                  preset=params.get("preset", "veryfast"),
                                                  scale=params.get("scale", 1.0))
                break
            params = selector.adjust_on_quality(params, is_image, low_quality=low_q)

    total_ms = int((time.perf_counter() - t0) * 1000)
    if feat:
        explanation = selector.explain(cls, conf, attempts[-1]["params"], feat)
    else:
        explanation = f"Fixed baseline params={attempts[-1]['params']}"
    return {"out": out_path, "orig_size": _size(src), "new_size": _size(out_path),
            "attempts": attempts, "best": attempts[-1], "total_ms": total_ms,
            "explanation": explanation, "class": cls}
