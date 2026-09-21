"""AI param selector: class -> quality/CRF. Fast rule model + binary-search retry."""

CLASS_PRESET = {
    "graphic-screen":   {"format": "webp", "quality": 85, "crf": 20},
    "smooth-lowdetail": {"format": "webp", "quality": 70, "crf": 28},
    "textured":         {"format": "webp", "quality": 82, "crf": 24},
    "photo-natural":    {"format": "webp", "quality": 78, "crf": 25},
}

def predict_image_params(cls, mp):
    base = CLASS_PRESET.get(cls, CLASS_PRESET["photo-natural"]).copy()
    # big images: allow slightly lower quality + downscale hint
    scale = 1.0
    if mp > 12_000_000:
        scale = 0.75
    elif mp > 4_000_000:
        scale = 0.85
    base["scale"] = scale
    return base

def predict_video_params(cls):
    base = CLASS_PRESET.get(cls, CLASS_PRESET["photo-natural"]).copy()
    return {"codec": "libx264", "crf": base["crf"], "preset": "veryfast", "scale": 1.0}

def adjust_on_quality(params, is_image, low_quality: bool):
    p = dict(params)
    if is_image:
        p["quality"] = min(95, p["quality"] + 8) if low_quality else max(40, p["quality"] - 8)
    else:
        p["crf"] = max(18, p["crf"] - 3) if low_quality else min(33, p["crf"] + 2)
    return p

def explain(cls, conf, params, feat):
    return (f"Class={cls} (conf {conf}); texture={feat['texture']}, "
            f"entropy={feat['entropy']}, color={feat['color']} -> {params}")
