#!/usr/bin/env python3
import os, socket
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
try:
    with open('/sys/class/graphics/fb0/virtual_size') as f:
        w_s, h_s = f.read().strip().split(',')
        W, H = int(w_s), int(h_s)
except: pass

scale = H / 1080.0
hostname = socket.gethostname()

# 1. Saf Derin Siyah Arka Plan (OLED Black)
img = Image.new('RGB', (W, H), '#000000')
draw = ImageDraw.Draw(img)

# Zarif Apple Monokrom Derinlik Işığı
for r in range(int(450 * scale), 0, -int(15 * scale)):
    val = int(4 + (450*scale-r)*0.035)
    draw.ellipse([W//2 - r*2, H//2 - r - int(40*scale), W//2 + r*2, H//2 + r - int(40*scale)], fill=(val, val, val))

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

try:
    f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(76 * scale))
    f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(34 * scale))
    f_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(26 * scale))
    f_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(32 * scale))
    f_val = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(46 * scale))
    f_pin = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(60 * scale))
    f_footer = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(24 * scale))
except:
    f_title = ImageFont.load_default()
    f_sub = f_badge = f_label = f_val = f_pin = f_footer = f_title

def draw_centered_text(y, text, font, fill):
    try:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except: tw, th = draw.textsize(text, font=font)
    draw.text((W//2 - tw//2, y - th//2), text, fill=fill, font=font)

# 1. Rozet (Koyu Kömür ve Gümüş)
bw, bh = int(460 * scale), int(52 * scale)
bx1, by1 = (W - bw)//2, int(90 * scale)
draw_round_rect([bx1, by1, bx1 + bw, by1 + bh], radius=bh//2, fill='#1c1c1e', outline='#3a3a3c', width=1)
draw_centered_text(by1 + bh//2, "Hazir / Ready", f_badge, "#f5f5f7")

# 3. 40dp Kavisli Titanyum Kart
cw, ch = int(1060 * scale), int(510 * scale)
radius = int(40 * scale)
cx1, cy1 = (W - cw)//2, int(350 * scale)
draw_round_rect([cx1, cy1, cx1 + cw, cy1 + ch], radius=radius, fill='#121214', outline='#2c2c2e', width=2)

# Satır 1: Cihaz Adı
r1_y = cy1 + int(105 * scale)
draw.text((cx1 + int(70*scale), r1_y - int(18*scale)), "Cihaz Adi / Device", fill="#a1a1a6", font=f_label)
p_w, p_h = int(460 * scale), int(74 * scale)
px1, py1 = cx1 + cw - p_w - int(60*scale), r1_y - p_h//2
draw_round_rect([px1, py1, px1 + p_w, py1 + p_h], radius=p_h//2, fill='#1c1c1e', outline='#3a3a3c', width=1)

try:
    bbox = f_val.getbbox(hostname)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
except: tw, th = draw.textsize(hostname, font=f_val)
draw.text((px1 + (p_w - tw)//2, py1 + (p_h - th)//2 - int(4*scale)), hostname, fill="#ffffff", font=f_val)

# Satır 2: PIN Kodu (Saf Beyaz Vurgulu)
r2_y = cy1 + int(255 * scale)
draw.text((cx1 + int(70*scale), r2_y - int(18*scale)), "PIN", fill="#a1a1a6", font=f_label)
px2, py2 = cx1 + cw - p_w - int(60*scale), r2_y - p_h//2
draw_round_rect([px2, py2, px2 + p_w, py2 + p_h], radius=p_h//2, fill='#1c1c1e', outline='#48484a', width=2)

pin_str = "31415926"
try:
    bbox = f_pin.getbbox(pin_str)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((px2 + (p_w - tw)//2, py2 + (p_h - th)//2 - int(5*scale)), pin_str, fill="#ffffff", font=f_pin)
except:
    draw.text((px2 + 80, py2 + 15), pin_str, fill="#ffffff", font=f_pin)

# Satır 3: Video Akışı
r3_y = cy1 + int(405 * scale)
draw.text((cx1 + int(70*scale), r3_y - int(18*scale)), "Video", fill="#a1a1a6", font=f_label)
px3, py3 = cx1 + cw - p_w - int(60*scale), r3_y - p_h//2
draw_round_rect([px3, py3, px3 + p_w, py3 + p_h], radius=p_h//2, fill='#1c1c1e', outline='#2c2c2e', width=1)

m_str = f"Player 2 ({W}x{H})"
try:
    bbox = f_label.getbbox(m_str)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((px3 + (p_w - tw)//2, py3 + (p_h - th)//2 - int(4*scale)), m_str, fill="#e5e5ea", font=f_label)
except:
    draw.text((px3 + 40, py3 + 15), m_str, fill="#e5e5ea", font=f_label)

# Alt Bilgi
draw_centered_text(int(960 * scale), "Android & Windows Miracast Compatible/Uyumlu , Github.com/EfeAtesh", f_footer, "#636366")

out_path = os.path.expanduser('~/lazycast_setup/lazycast/splash.png')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
img.save(out_path)
print(f"Monochrome Apple splash saved to {out_path}")
