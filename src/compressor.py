"""Compression primitives: Pillow for images, ffmpeg subprocess for video."""
import subprocess
import os
from PIL import Image


def compress_image(src, dst, quality=78, img_format="webp", scale=1.0):
    im = Image.open(src).convert("RGB")
    if scale < 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)))
    fmt = img_format.upper()
    kw = {"quality": int(quality), "method": 4} if fmt == "WEBP" else {"quality": int(quality), "optimize": True}
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    im.save(dst, fmt, **kw)
    return dst


def compress_video(src, dst, crf=25, preset="veryfast", scale=1.0):
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    vf = None
    if scale < 1.0:
        vf = f"scale=iw*{scale}:ih*{scale}"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src,
           "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
           "-c:a", "aac", "-b:a", "128k"]
    if vf:
        cmd += ["-vf", vf]
    cmd += [dst]
    subprocess.run(cmd, check=True)
    return dst
