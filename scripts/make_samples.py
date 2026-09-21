"""Create demo samples without network: gradient photo + graphic + short mp4 (ffmpeg testsrc)."""
import os
import subprocess
from PIL import Image
import numpy as np
os.makedirs("data/samples", exist_ok=True)
# photo-like horizontal gradient (red channel) shifted for green; blue is flat
a = np.tile(np.linspace(0, 255, 512, dtype=np.uint8), (512, 1))
img = np.stack([a, np.roll(a, 100, 1), np.full_like(a, 128)], -1)
Image.fromarray(img.astype("uint8")).save("data/samples/photo.jpg", quality=95)
# graphic: flat + text-ish bars
g = np.full((400, 600, 3), 255, np.uint8); g[100:150, :] = [30, 120, 220]; g[200:260, 50:550] = [20, 20, 20]
Image.fromarray(g).save("data/samples/graphic.png")
# video: 5s 640x360 testsrc
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                "testsrc=duration=5:size=640x360:rate=30",
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                "data/samples/clip.mp4"], check=True)
print("samples ready:", os.listdir("data/samples"))
