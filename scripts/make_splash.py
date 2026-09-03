#!/usr/bin/env python3
import os, socket
from PIL import Image, ImageDraw, ImageFont

# 1. Detect Real Screen Resolution Dynamically
W, H = 1920, 1080
try:
    with open('/sys/class/graphics/fb0/virtual_size') as f:
        w_s, h_s = f.read().strip().split(',')
        W, H = int(w_s), int(h_s)
except: pass

scale = H / 1080.0
hostname = socket.gethostname()

img = Image.new('RGB', (W, H), '#080d1a')
draw = ImageDraw.Draw(img)

# Custom 100% Compatible 40dp Rounded Rectangle Helper
def draw_round_rect(box, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = box
    r = radius
    d = 2 * r
    if fill:
        draw.pieslice([x1, y1, x1 + d, y1 + d], 180, 270, fill=fill)
        draw.pieslice([x2 - d, y1, x2, y1 + d], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - d, x1 + d, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - d, y2 - d, x2, y2], 0, 90, fill=fill)
        draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
        draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)
    if outline and width > 0:
        draw.line([x1 + r, y1, x2 - r, y1], fill=outline, width=width)
        draw.line([x1 + r, y2, x2 - r, y2], fill=outline, width=width)
        draw.line([x1, y1 + r, x1, y2 - r], fill=outline, width=width)
        draw.line([x2, y1 + r, x2, y2 - r], fill=outline, width=width)
        draw.arc([x1, y1, x1 + d, y1 + d], 180, 270, fill=outline, width=width)
        draw.arc([x2 - d, y1, x2, y1 + d], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - d, x1 + d, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - d, y2 - d, x2, y2], 0, 90, fill=outline, width=width)

# Ambient Radial Light
for r in range(int(500 * scale), 0, -int(12 * scale)):
    alpha_color = (int(12 + (500*scale-r)*0.04), int(22 + (500*scale-r)*0.08), int(48 + (500*scale-r)*0.15))
    draw.ellipse([W//2 - r*2, H//2 - r - int(50*scale), W//2 + r*2, H//2 + r - int(50*scale)], fill=alpha_color)

# Crisp TrueType Vector Fonts
try:
    f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(80 * scale))
    f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(38 * scale))
    f_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * scale))
    f_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(34 * scale))
    f_val = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(48 * scale))
    f_pin = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(64 * scale))
    f_footer = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(26 * scale))
except:
    f_title = ImageFont.load_default()
    f_sub = f_badge = f_label = f_val = f_pin = f_footer = f_title

def draw_centered_text(y, text, font, fill):
    try:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        tw, th = draw.textsize(text, font=font)
    draw.text((W//2 - tw//2, y - th//2), text, fill=fill, font=font)

# 1. Top Badge
bw, bh = int(500 * scale), int(58 * scale)
bx1, by1 = (W - bw)//2, int(80 * scale)
draw_round_rect([bx1, by1, bx1 + bw, by1 + bh], radius=int(28 * scale), fill='#1e293b', outline='#3b82f6', width=2)
draw_centered_text(by1 + bh//2, "● WIRELESS DISPLAY RECEIVER", f_badge, "#60a5fa")

# 2. Huge Header Title
draw_centered_text(int(200 * scale), "Yayina Hazir  •  Ready to Cast", f_title, "#ffffff")
draw_centered_text(int(265 * scale), "Smart View veya Ekran Yansit ile baglanin", f_sub, "#94a3b8")

# 3. Main 40dp Card
cw, ch = int(1080 * scale), int(520 * scale)
radius = int(40 * scale)
cx1, cy1 = (W - cw)//2, int(350 * scale)
draw_round_rect([cx1, cy1, cx1 + cw, cy1 + ch], radius=radius, fill='#111827', outline='#374151', width=3)

# Row 1: Cihaz Adi
r1_y = cy1 + int(110 * scale)
draw.text((cx1 + int(70*scale), r1_y - int(20*scale)), "Cihaz Adi / Device:", fill="#9ca3af", font=f_label)
p_w, p_h = int(460 * scale), int(76 * scale)
px1, py1 = cx1 + cw - p_w - int(60*scale), r1_y - p_h//2
draw_round_rect([px1, py1, px1 + p_w, py1 + p_h], radius=int(20*scale), fill='#1f2937', outline='#3b82f6', width=2)

try:
    bbox = f_val.getbbox(hostname)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
except: tw, th = draw.textsize(hostname, font=f_val)
draw.text((px1 + (p_w - tw)//2, py1 + (p_h - th)//2 - int(4*scale)), hostname, fill="#38bdf8", font=f_val)

# Row 2: PIN Kodu
r2_y = cy1 + int(260 * scale)
draw.text((cx1 + int(70*scale), r2_y - int(20*scale)), "WPS PIN Kodu:", fill="#9ca3af", font=f_label)
px2, py2 = cx1 + cw - p_w - int(60*scale), r2_y - p_h//2
draw_round_rect([px2, py2, px2 + p_w, py2 + p_h], radius=int(20*scale), fill='#1f2937', outline='#22c55e', width=3)

pin_str = "31415926"
try:
    bbox = f_pin.getbbox(pin_str)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
except: tw, th = draw.textsize(pin_str, font=f_pin)
draw.text((px2 + (p_w - tw)//2, py2 + (p_h - th)//2 - int(6*scale)), pin_str, fill="#4ade80", font=f_pin)

# Row 3: Video Akisi
r3_y = cy1 + int(410 * scale)
draw.text((cx1 + int(70*scale), r3_y - int(20*scale)), "Video Motoru:", fill="#9ca3af", font=f_label)
px3, py3 = cx1 + cw - p_w - int(60*scale), r3_y - p_h//2
draw_round_rect([px3, py3, px3 + p_w, py3 + p_h], radius=int(18*scale), fill='#1e293b')

m_str = f"Player 2 ({W}x{H})"
try:
    bbox = f_label.getbbox(m_str)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
except: tw, th = draw.textsize(m_str, font=f_label)
draw.text((px3 + (p_w - tw)//2, py3 + (p_h - th)//2 - int(4*scale)), m_str, fill="#f1f5f9", font=f_label)

# Footer
draw_centered_text(int(960 * scale), "Android (Smart View / Xiaomi / Huawei) & Windows Miracast Uyumlu", f_footer, "#64748b")

out_path = os.path.expanduser('~/lazycast_setup/lazycast/splash.png')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
img.save(out_path)
print(f"Dynamic splash ({W}x{H}) created at {out_path}!")
