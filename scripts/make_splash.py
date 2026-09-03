import os, socket
from PIL import Image, ImageDraw

W, H = 1920, 1080
hostname = socket.gethostname()

img = Image.new('RGB', (W, H), '#0b0f19')
draw = ImageDraw.Draw(img)

# Ambient glow
for r in range(400, 0, -5):
    draw.ellipse([W//2 - r*2, H//2 - r - 50, W//2 + r*2, H//2 + r - 50], fill=(15, 23, 42))

# Header Badge
draw.rectangle([W//2 - 180, 180, W//2 + 180, 240], fill='#1e293b', outline='#3b82f6', width=2)
draw.text((W//2, 210), "WIRELESS DISPLAY", fill="#60a5fa", anchor="mm")

# Title
draw.text((W//2, 330), "Yayina Hazir / Ready to Cast", fill="#ffffff", anchor="mm")
draw.text((W//2, 400), "Smart View veya Ekran Yansit ile baglanin", fill="#94a3b8", anchor="mm")

# Info Box
bx1, by1, bx2, by2 = (W - 700) // 2, 480, (W + 700) // 2, 740
draw.rectangle([bx1, by1, bx2, by2], fill='#111827', outline='#374151', width=3)

draw.text((bx1 + 50, by1 + 75), "Cihaz / Device:", fill="#9ca3af", anchor="lm")
draw.rectangle([bx2 - 280, by1 + 45, bx2 - 40, by1 + 105], fill='#1f2937')
draw.text((bx2 - 160, by1 + 75), f"{hostname}", fill="#38bdf8", anchor="mm")

draw.text((bx1 + 50, by1 + 185), "WPS PIN:", fill="#9ca3af", anchor="lm")
draw.rectangle([bx2 - 280, by1 + 155, bx2 - 40, by1 + 215], fill='#1f2937')
draw.text((bx2 - 160, by1 + 185), "31415926", fill="#4ade80", anchor="mm")

draw.text((W//2, 920), "* Android / Samsung Smart View / Windows Miracast Compatible *", fill="#475569", anchor="mm")

img.save(os.path.expanduser('~/lazycast_setup/lazycast/splash.png'))
