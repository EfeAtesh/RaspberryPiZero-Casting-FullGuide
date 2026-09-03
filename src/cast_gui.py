#!/usr/bin/env python3
"""
=============================================================================
Raspberry Pi Zero 2 W - Wireless Cast Control Center (Apple Monochrome UI)
Author: Efe Atesh (Github.com/EfeAtesh)
=============================================================================
"""
import os, sys, time, socket, subprocess, re, math

# Framebuffer doğrudan çizim sürücüleri
os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"

import pygame

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Cast Control Center")
clock = pygame.time.Clock()

# TrueType / Vektör Fontlar
FONT_TITLE = pygame.font.Font(None, 68)
FONT_SUB = pygame.font.Font(None, 28)
FONT_CARD = pygame.font.Font(None, 34)
FONT_TEXT = pygame.font.Font(None, 26)
FONT_BTN = pygame.font.Font(None, 26)

LANG_FILE = os.path.expanduser("~/.cast_lang")
LANG = "TR"
if os.path.exists(LANG_FILE):
    try:
        with open(LANG_FILE) as f: LANG = f.read().strip() or "TR"
    except: pass

def get_sys_info():
    ip = "Yok / None"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except: pass
    temp = "N/A"
    try: temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode().replace("temp=","").strip()
    except: pass
    wifi = "Bagli Degil / Disconnected"
    try:
        out = subprocess.check_output("sudo iwgetid -r 2>/dev/null", shell=True).decode().strip()
        if out: wifi = out
    except: pass
    return {"ip": ip, "temp": temp, "wifi": wifi, "host": socket.gethostname()}

def scan_wifi():
    ssids = []
    try:
        out = subprocess.check_output("sudo iwlist wlan0 scan 2>/dev/null", shell=True).decode(errors="ignore")
        for s in re.findall(r'ESSID:"([^"]+)"', out):
            if s and s not in ssids: ssids.append(s)
    except: pass
    return ssids

def scan_bt():
    devices = []
    try:
        subprocess.run("sudo rfkill unblock bluetooth && sudo systemctl start bluetooth", shell=True)
        p = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        p.communicate(input="power on\nscan on\n", timeout=6)
    except: pass
    try:
        out = subprocess.check_output("bluetoothctl devices", shell=True).decode(errors="ignore")
        for line in out.strip().split("\n"):
            if "Device" in line:
                p = line.split()
                if len(p) >= 3: devices.append((p[1], " ".join(p[2:])))
    except: pass
    return devices

# 40dp Kavisli Kart Çizici (Apple TV Tarzı)
def draw_rounded_card(surface, color, rect, radius=40, border_color=(44, 44, 46), border_width=1):
    pygame.draw.circle(surface, color, (rect.left + radius, rect.top + radius), radius)
    pygame.draw.circle(surface, color, (rect.right - radius, rect.top + radius), radius)
    pygame.draw.circle(surface, color, (rect.left + radius, rect.bottom - radius), radius)
    pygame.draw.circle(surface, color, (rect.right - radius, rect.bottom - radius), radius)

    pygame.draw.rect(surface, color, (rect.left + radius, rect.top, rect.width - 2 * radius, rect.height))
    pygame.draw.rect(surface, color, (rect.left, rect.top + radius, rect.width, rect.height - 2 * radius))

    if border_color and border_width > 0:
        pygame.draw.line(surface, border_color, (rect.left + radius, rect.top), (rect.right - radius, rect.top), border_width)
        pygame.draw.line(surface, border_color, (rect.left + radius, rect.bottom), (rect.right - radius, rect.bottom), border_width)
        pygame.draw.line(surface, border_color, (rect.left, rect.top + radius), (rect.left, rect.bottom - radius), border_width)
        pygame.draw.line(surface, border_color, (rect.right, rect.top + radius), (rect.right, rect.bottom - radius), border_width)

        pygame.draw.arc(surface, border_color, (rect.left, rect.top, 2*radius, 2*radius), math.pi/2, math.pi, border_width)
        pygame.draw.arc(surface, border_color, (rect.right - 2*radius, rect.top, 2*radius, 2*radius), 0, math.pi/2, border_width)
        pygame.draw.arc(surface, border_color, (rect.left, rect.bottom - 2*radius, 2*radius, 2*radius), math.pi, 3*math.pi/2, border_width)
        pygame.draw.arc(surface, border_color, (rect.right - 2*radius, rect.bottom - 2*radius, 2*radius, 2*radius), 3*math.pi/2, 2*math.pi, border_width)

def draw_btn(surface, color, rect, text, radius=20, border_color=None, font=FONT_CARD, text_color=(255, 255, 255)):
    draw_rounded_card(surface, color, rect, radius=radius, border_color=border_color, border_width=1 if border_color else 0)
    txt = font.render(text, True, text_color)
    surface.blit(txt, txt.get_rect(center=rect.center))

MODAL = None
WIFI_LIST = []
BT_LIST = []
CUR_SSID = ""
PASS_INPUT = ""
info = get_sys_info()
running = True

while running:
    clock.tick(30)
    mpos = pygame.mouse.get_pos()
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT: running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if MODAL: MODAL = None
                else: running = False
            elif MODAL == "PASS":
                if e.key == pygame.K_RETURN:
                    cmd = "sudo wpa_cli -i wlan0 add_network && sudo wpa_cli -i wlan0 set_network 0 ssid '\"" + str(CUR_SSID) + "\"' && sudo wpa_cli -i wlan0 set_network 0 psk '\"" + str(PASS_INPUT) + "\"' && sudo wpa_cli -i wlan0 enable_network 0 && sudo wpa_cli -i wlan0 save_config"
                    subprocess.run(cmd, shell=True)
                    MODAL = None
                elif e.key == pygame.K_BACKSPACE: PASS_INPUT = PASS_INPUT[:-1]
                elif e.unicode.isprintable(): PASS_INPUT += e.unicode

    # 1. Saf Derin Siyah Arka Plan (OLED Black)
    screen.fill((0, 0, 0))

    # Üst Saat ve "Change Language" Butonu
    clock_t = FONT_SUB.render(time.strftime("%H:%M"), True, (134, 134, 139))
    screen.blit(clock_t, (WIDTH - 120, 30))

    lang_r = pygame.Rect(WIDTH - 400, 24, 250, 44)
    draw_btn(screen, (44, 44, 46) if lang_r.collidepoint(mpos) else (28, 28, 30), lang_r, f"Change Language [{LANG}]", radius=14, border_color=(58, 58, 60), font=FONT_BTN)
    if any(e.type == pygame.MOUSEBUTTONDOWN and lang_r.collidepoint(mpos) for e in events):
        LANG = "EN" if LANG == "TR" else "TR"
        with open(LANG_FILE, "w") as f: f.write(LANG)

    # Başlık ve İpuçları
    t = FONT_TITLE.render("Menü" if LANG=="TR" else "Menu", True, (255, 255, 255))
    screen.blit(t, t.get_rect(center=(WIDTH//2, 100)))
    sub = FONT_SUB.render("Cihaz/Device " + str(info['host']) + "   |   PIN 31415926   |  Burada USB Mouse kullanabilirsiniz, aparatla takmak gerekebilir. / You can use USB Mouse here, you may need to use an adapter.", True, (161, 161, 166))
    screen.blit(sub, sub.get_rect(center=(WIDTH//2, 155)))

    # 3 Modern 40dp Titanyum Kart (#121214)
    cw, ch = 520, 460
    start_x = (WIDTH - (cw*3 + 120)) // 2

    # Kart 1: Wi-Fi
    c1 = pygame.Rect(start_x, 230, cw, ch)
    c1_hover = c1.collidepoint(mpos)
    draw_rounded_card(screen, (18, 18, 20), c1, radius=40, border_color=(72, 72, 74) if c1_hover else (44, 44, 46), border_width=2 if c1_hover else 1)
    
    screen.blit(FONT_CARD.render("Wi-Fi", True, (255, 255, 255)), (start_x+40, 265))
    screen.blit(FONT_TEXT.render("Ag / Network:", True, (161, 161, 166)), (start_x+40, 335))
    screen.blit(FONT_CARD.render(info["wifi"][:22], True, (255, 255, 255)), (start_x+40, 370))
    screen.blit(FONT_TEXT.render("IP:", True, (161, 161, 166)), (start_x+40, 440))
    screen.blit(FONT_CARD.render(info["ip"], True, (255, 255, 255)), (start_x+40, 475))

    btn_w = pygame.Rect(start_x+40, 570, cw-80, 60)
    btn_w_hover = btn_w.collidepoint(mpos)
    draw_btn(screen, (44, 44, 46) if btn_w_hover else (28, 28, 30), btn_w, "Aglari Tara / Scan", radius=20, border_color=(72, 72, 74) if btn_w_hover else (58, 58, 60))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_w_hover for e in events):
        WIFI_LIST = scan_wifi()
        MODAL = "WIFI"

    # Kart 2: Bluetooth (Manuel Tarama)
    c2 = pygame.Rect(start_x + cw + 60, 230, cw, ch)
    c2_hover = c2.collidepoint(mpos)
    draw_rounded_card(screen, (18, 18, 20), c2, radius=40, border_color=(72, 72, 74) if c2_hover else (44, 44, 46), border_width=2 if c2_hover else 1)

    screen.blit(FONT_CARD.render("Bluetooth Klavye / Fare", True, (255, 255, 255)), (c2.x+40, 265))
    screen.blit(FONT_TEXT.render("Bluetooth 4.2 BLE:", True, (161, 161, 166)), (c2.x+40, 335))
    screen.blit(FONT_CARD.render("Hazir / Ready", True, (255, 255, 255)), (c2.x+40, 370))
    screen.blit(FONT_TEXT.render("Kablosuz klavye ve fareleri" if LANG=="TR" else "Pair wireless keyboard/mouse", True, (161, 161, 166)), (c2.x+40, 440))
    screen.blit(FONT_TEXT.render("tek tikla eslestirebilirsiniz." if LANG=="TR" else "with one click.", True, (161, 161, 166)), (c2.x+40, 470))

    btn_b = pygame.Rect(c2.x+40, 570, cw-80, 60)
    btn_b_hover = btn_b.collidepoint(mpos)
    draw_btn(screen, (44, 44, 46) if btn_b_hover else (28, 28, 30), btn_b, "Cihaz Tara / Pair", radius=20, border_color=(72, 72, 74) if btn_b_hover else (58, 58, 60))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_b_hover for e in events):
        BT_LIST = scan_bt()
        MODAL = "BT"

    # Kart 3: Sistem Bilgisi
    c3 = pygame.Rect(start_x + (cw + 60)*2, 230, cw, ch)
    c3_hover = c3.collidepoint(mpos)
    draw_rounded_card(screen, (18, 18, 20), c3, radius=40, border_color=(72, 72, 74) if c3_hover else (44, 44, 46), border_width=2 if c3_hover else 1)

    screen.blit(FONT_CARD.render("Sistem Bilgisi" if LANG=="TR" else "System Health", True, (255, 255, 255)), (c3.x+40, 265))
    screen.blit(FONT_TEXT.render("CPU Sicaklik / Temp:", True, (161, 161, 166)), (c3.x+40, 335))
    screen.blit(FONT_CARD.render(info["temp"], True, (255, 255, 255)), (c3.x+40, 370))
    screen.blit(FONT_TEXT.render("GPU VRAM:", True, (161, 161, 166)), (c3.x+40, 440))
    screen.blit(FONT_CARD.render("256 MB (VideoCore IV)", True, (255, 255, 255)), (c3.x+40, 475))

    btn_r = pygame.Rect(c3.x+40, 570, cw-80, 60)
    btn_r_hover = btn_r.collidepoint(mpos)
    draw_btn(screen, (44, 44, 46) if btn_r_hover else (28, 28, 30), btn_r, "Yeniden Baslat / Reboot", radius=20, border_color=(72, 72, 74) if btn_r_hover else (58, 58, 60))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_r_hover for e in events):
        subprocess.run("sudo reboot", shell=True)

    # Alt Buton: Yayına Başla (Apple Minimalist Pill)
    btn_start = pygame.Rect(WIDTH//2 - 270, HEIGHT - 180, 540, 72)
    btn_start_hover = btn_start.collidepoint(mpos)
    draw_btn(screen, (245, 245, 247) if btn_start_hover else (225, 225, 230), btn_start, "YAYINA BASLA (START CAST)", radius=36, text_color=(0, 0, 0))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_start_hover for e in events):
        running = False

    # Alt İmzalı Bilgi
    footer_t = FONT_TEXT.render("Android & Windows Miracast Compatible/Uyumlu , Github.com/EfeAtesh", True, (99, 99, 102))
    screen.blit(footer_t, footer_t.get_rect(center=(WIDTH//2, HEIGHT - 60)))

    # Açılır Pencereler (Modals)
    if MODAL:
        m_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        m_bg.fill((0, 0, 0, 220))
        screen.blit(m_bg, (0, 0))
        mbox = pygame.Rect(WIDTH//2 - 420, HEIGHT//2 - 290, 840, 580)
        draw_rounded_card(screen, (18, 18, 20), mbox, radius=40, border_color=(58, 58, 60), border_width=2)

        close_r = pygame.Rect(mbox.right - 65, mbox.top + 20, 42, 42)
        draw_btn(screen, (44, 44, 46), close_r, "X", radius=14, border_color=(58, 58, 60))
        if any(e.type == pygame.MOUSEBUTTONDOWN and close_r.collidepoint(mpos) for e in events):
            MODAL = None

        if MODAL == "WIFI":
            screen.blit(FONT_CARD.render("Wi-Fi Agini Seciniz. / Select Wi-Fi Network", True, (255, 255, 255)), (mbox.x+50, mbox.top+35))
            if not WIFI_LIST: screen.blit(FONT_TEXT.render("Ag bulunamadi / No networks found", True, (161, 161, 166)), (mbox.x+50, mbox.top+120))
            for idx, s in enumerate(WIFI_LIST[:6]):
                ir = pygame.Rect(mbox.x+50, mbox.top+95+idx*72, mbox.w-100, 58)
                ir_hover = ir.collidepoint(mpos)
                draw_btn(screen, (44, 44, 46) if ir_hover else (28, 28, 30), ir, s, radius=18, border_color=(58, 58, 60))
                if any(e.type == pygame.MOUSEBUTTONDOWN and ir_hover for e in events):
                    CUR_SSID = s
                    PASS_INPUT = ""
                    MODAL = "PASS"

        elif MODAL == "PASS":
            screen.blit(FONT_CARD.render("[" + str(CUR_SSID) + "] Sifresi:", True, (255, 255, 255)), (mbox.x+50, mbox.top+45))
            inpr = pygame.Rect(mbox.x+50, mbox.top+180, mbox.w-100, 64)
            draw_rounded_card(screen, (28, 28, 30), inpr, radius=20, border_color=(72, 72, 74), border_width=2)
            pmask = "*"*len(PASS_INPUT)
            screen.blit(FONT_CARD.render(pmask if pmask else "Klavyeyle sifreyi yazip Enter'a basin / Type password & Enter", True, (255, 255, 255) if pmask else (134, 134, 139)), (inpr.x+25, inpr.y+18))

        elif MODAL == "BT":
            screen.blit(FONT_CARD.render("Bulunan Bluetooth Cihazlar / Found Bluetooth Devices", True, (255, 255, 255)), (mbox.x+50, mbox.top+35))
            if not BT_LIST: screen.blit(FONT_TEXT.render("Cihaz bulunamadi. Klavyenizi eslestirme moduna alin / No devices found. Turn on pairing mode.", True, (161, 161, 166)), (mbox.x+50, mbox.top+120))
            for idx, (mac, name) in enumerate(BT_LIST[:5]):
                ir = pygame.Rect(mbox.x+50, mbox.top+95+idx*82, mbox.w-100, 68)
                draw_rounded_card(screen, (28, 28, 30), ir, radius=20, border_color=(58, 58, 60))
                screen.blit(FONT_TEXT.render(name, True, (255, 255, 255)), (ir.x+20, ir.y+12))
                screen.blit(FONT_TEXT.render(mac, True, (161, 161, 166)), (ir.x+20, ir.y+38))
                pr = pygame.Rect(ir.right-160, ir.y+14, 140, 42)
                draw_btn(screen, (245, 245, 247), pr, "Eslestir / Pair", radius=14, text_color=(0, 0, 0))
                if any(e.type == pygame.MOUSEBUTTONDOWN and pr.collidepoint(mpos) for e in events):
                    subprocess.run(f"echo -e 'trust {mac}\\npair {mac}\\nconnect {mac}\\n' | bluetoothctl", shell=True)
                    MODAL = None

    pygame.display.flip()

pygame.quit()
