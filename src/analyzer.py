"""Feature extraction (numpy+PIL only) + content classification."""
import numpy as np
from PIL import Image

def features(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    small = im.resize((256, 256)).convert("L")
    a = np.asarray(small, dtype=np.float64)
    # texture: Laplacian variance
    lap = np.abs(a[2:, 1:-1] + a[:-2, 1:-1] + a[1:-1, 2:] + a[1:-1, :-2] - 4 * a[1:-1, 1:-1])
    texture = float(lap.var())
    # edge density: Sobel-ish gradient
    gx = np.abs(a[:, 2:] - a[:, :-2]).mean()
    # colorfulness: R-G,B variance
    rgb = np.asarray(im.resize((64, 64)), dtype=np.float64)
    colorfulness = float(rgb.std())
    # entropy of luminance hist
    hist, _ = np.histogram(a, bins=32, density=True)
    hist = hist[hist > 0]
    entropy = float(-(hist * np.log2(hist)).sum())
    mp = w * h
    return {"w": w, "h": h, "mp": mp, "texture": round(texture, 2),
            "edge": round(float(gx), 2), "color": round(colorfulness, 2),
            "entropy": round(entropy, 2)}

def classify(f):
    # tiny rule-based "AI" (replaceable by sklearn/CNN later)
    if f["color"] < 8 and f["edge"] > 25:
        return "graphic-screen", 0.85
    if f["texture"] < 30 and f["entropy"] < 4.2:
        return "smooth-lowdetail", 0.80
    if f["texture"] > 800:
        return "textured", 0.82
    if f["entropy"] > 5.4 and f["color"] > 30:
        return "photo-natural", 0.78
    return "photo-natural", 0.60
