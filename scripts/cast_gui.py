#!/usr/bin/env python3
import os, sys, time, socket, subprocess, re

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"

import pygame

pygame.init()
pygame.font.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Cast Control Center")
clock = pygame.time.Clock()

FONT_TITLE = pygame.font.Font(None, 64)
FONT_SUB = pygame.font.Font(None, 36)
FONT_CARD = pygame.font.Font(None, 34)
FONT_TEXT = pygame.font.Font(None, 28)

LANG_FILE = os.path.expanduser("~/.cast_lang")
LANG = "TR"
if os.path.exists(LANG_FILE):
    try:
        with open(LANG_FILE) as f: LANG = f.read().strip() or "TR"
    except: pass

def get_sys_info():
    ip = "Yok"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except: pass
    temp = "N/A"
    try: temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode().replace("temp=","").strip()
    except: pass
    wifi = "Bagli Degil"
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

    # Koyu Modern Gradyan Arka Plan
    for y in range(0, HEIGHT, 4):
        c = int(12 + (y/HEIGHT)*20)
        pygame.draw.rect(screen, (c, c+5, c+15), (0, y, WIDTH, 4))

    # Ust Bilgi ve Dil Butonu
    clock_t = FONT_SUB.render(time.strftime("%H:%M"), True, (148, 163, 184))
    screen.blit(clock_t, (WIDTH - 120, 30))

    lang_r = pygame.Rect(WIDTH - 300, 25, 140, 40)
    pygame.draw.rect(screen, (51, 65, 85) if lang_r.collidepoint(mpos) else (30, 41, 59), lang_r)
    ltxt = FONT_TEXT.render("[ " + str(LANG) + " ]", True, (248, 250, 252))
    screen.blit(ltxt, ltxt.get_rect(center=lang_r.center))
    if any(e.type == pygame.MOUSEBUTTONDOWN and lang_r.collidepoint(mpos) for e in events):
        LANG = "EN" if LANG == "TR" else "TR"
        with open(LANG_FILE, "w") as f: f.write(LANG)

    # Baslik
    t = FONT_TITLE.render("Yayina Hazir" if LANG=="TR" else "Ready to Cast", True, (248, 250, 252))
    screen.blit(t, t.get_rect(center=(WIDTH//2, 110)))
    sub = FONT_SUB.render("Cihaz: " + str(info['host']) + "   |   PIN: 31415926   |   Motor: Player 2 (1080p)", True, (148, 163, 184))
    screen.blit(sub, sub.get_rect(center=(WIDTH//2, 165)))

    # 3 Modern Kart
    cw, ch = 520, 440
    start_x = (WIDTH - (cw*3 + 120)) // 2

    # Kart 1: Wi-Fi
    c1 = pygame.Rect(start_x, 240, cw, ch)
    pygame.draw.rect(screen, (17, 24, 39), c1)
    pygame.draw.rect(screen, (59, 130, 246) if c1.collidepoint(mpos) else (55, 65, 81), c1, 2)
    screen.blit(FONT_CARD.render("Wi-Fi Agi" if LANG=="TR" else "Wi-Fi Network", True, (255,255,255)), (start_x+30, 270))
    screen.blit(FONT_TEXT.render("Aktif Ag / SSID:", True, (148, 163, 184)), (start_x+30, 340))
    screen.blit(FONT_CARD.render(info["wifi"][:22], True, (56, 189, 248)), (start_x+30, 375))
    screen.blit(FONT_TEXT.render("IP Adresi:", True, (148, 163, 184)), (start_x+30, 440))
    screen.blit(FONT_CARD.render(info["ip"], True, (34, 197, 94)), (start_x+30, 475))

    btn_w = pygame.Rect(start_x+30, 580, cw-60, 60)
    pygame.draw.rect(screen, (59, 130, 246) if btn_w.collidepoint(mpos) else (37, 99, 235), btn_w)
    bt = FONT_CARD.render("Aglari Tara / Scan", True, (255,255,255))
    screen.blit(bt, bt.get_rect(center=btn_w.center))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_w.collidepoint(mpos) for e in events):
        WIFI_LIST = scan_wifi()
        MODAL = "WIFI"

    # Kart 2: Bluetooth
    c2 = pygame.Rect(start_x + cw + 60, 240, cw, ch)
    pygame.draw.rect(screen, (17, 24, 39), c2)
    pygame.draw.rect(screen, (59, 130, 246) if c2.collidepoint(mpos) else (55, 65, 81), c2, 2)
    screen.blit(FONT_CARD.render("Bluetooth Klavye / Fare", True, (255,255,255)), (c2.x+30, 270))
    screen.blit(FONT_TEXT.render("Bluetooth 4.2 BLE:", True, (148, 163, 184)), (c2.x+30, 340))
    screen.blit(FONT_CARD.render("Hazir / Ready", True, (34, 197, 94)), (c2.x+30, 375))
    screen.blit(FONT_TEXT.render("Kablosuz klavye ve fareleri" if LANG=="TR" else "Pair wireless keyboard/mouse", True, (148, 163, 184)), (c2.x+30, 440))
    screen.blit(FONT_TEXT.render("tek tikla eslestirebilirsiniz." if LANG=="TR" else "with one click.", True, (148, 163, 184)), (c2.x+30, 470))

    btn_b = pygame.Rect(c2.x+30, 580, cw-60, 60)
    pygame.draw.rect(screen, (59, 130, 246) if btn_b.collidepoint(mpos) else (37, 99, 235), btn_b)
    bb = FONT_CARD.render("Cihaz Tara / Pair", True, (255,255,255))
    screen.blit(bb, bb.get_rect(center=btn_b.center))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_b.collidepoint(mpos) for e in events):
        BT_LIST = scan_bt()
        MODAL = "BT"

    # Kart 3: Sistem Bilgisi
    c3 = pygame.Rect(start_x + (cw + 60)*2, 240, cw, ch)
    pygame.draw.rect(screen, (17, 24, 39), c3)
    pygame.draw.rect(screen, (59, 130, 246) if c3.collidepoint(mpos) else (55, 65, 81), c3, 2)
    screen.blit(FONT_CARD.render("Sistem Bilgisi" if LANG=="TR" else "System Health", True, (255,255,255)), (c3.x+30, 270))
    screen.blit(FONT_TEXT.render("CPU Sicaklik / Temp:", True, (148, 163, 184)), (c3.x+30, 340))
    screen.blit(FONT_CARD.render(info["temp"], True, (34, 197, 94)), (c3.x+30, 375))
    screen.blit(FONT_TEXT.render("GPU VRAM:", True, (148, 163, 184)), (c3.x+30, 440))
    screen.blit(FONT_CARD.render("256 MB (VideoCore IV)", True, (56, 189, 248)), (c3.x+30, 475))

    btn_r = pygame.Rect(c3.x+30, 580, cw-60, 60)
    pygame.draw.rect(screen, (225, 29, 72) if btn_r.collidepoint(mpos) else (185, 28, 28), btn_r)
    br = FONT_CARD.render("Yeniden Baslat / Reboot", True, (255,255,255))
    screen.blit(br, br.get_rect(center=btn_r.center))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_r.collidepoint(mpos) for e in events):
        subprocess.run("sudo reboot", shell=True)

    # Alt Buton: Yayina Basla
    btn_start = pygame.Rect(WIDTH//2 - 250, HEIGHT - 180, 500, 70)
    pygame.draw.rect(screen, (34, 197, 94) if btn_start.collidepoint(mpos) else (16, 185, 129), btn_start)
    bs = FONT_CARD.render(">> YAYINA BASLA (START CAST) <<", True, (255,255,255))
    screen.blit(bs, bs.get_rect(center=btn_start.center))
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_start.collidepoint(mpos) for e in events):
        running = False

    # Acilir Pencereler (Modals)
    if MODAL:
        m_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        m_bg.fill((0, 0, 0, 200))
        screen.blit(m_bg, (0, 0))
        mbox = pygame.Rect(WIDTH//2 - 400, HEIGHT//2 - 280, 800, 560)
        pygame.draw.rect(screen, (15, 23, 42), mbox)
        pygame.draw.rect(screen, (59, 130, 246), mbox, 2)

        # Kapat Butonu
        close_r = pygame.Rect(mbox.right - 50, mbox.top + 15, 35, 35)
        pygame.draw.rect(screen, (75, 85, 99), close_r)
        screen.blit(FONT_CARD.render("X", True, (255,255,255)), (close_r.x+8, close_r.y+4))
        if any(e.type == pygame.MOUSEBUTTONDOWN and close_r.collidepoint(mpos) for e in events):
            MODAL = None

        if MODAL == "WIFI":
            screen.blit(FONT_CARD.render("Wi-Fi Agini Secin", True, (255,255,255)), (mbox.x+40, mbox.top+30))
            if not WIFI_LIST: screen.blit(FONT_TEXT.render("Ag bulunamadi / No networks found.", True, (148, 163, 184)), (mbox.x+40, mbox.top+120))
            for idx, s in enumerate(WIFI_LIST[:6]):
                ir = pygame.Rect(mbox.x+40, mbox.top+90+idx*70, mbox.w-80, 55)
                pygame.draw.rect(screen, (30, 41, 59) if ir.collidepoint(mpos) else (17, 24, 39), ir)
                screen.blit(FONT_TEXT.render(s, True, (255,255,255)), (ir.x+20, ir.y+15))
                if any(e.type == pygame.MOUSEBUTTONDOWN and ir.collidepoint(mpos) for e in events):
                    CUR_SSID = s
                    PASS_INPUT = ""
                    MODAL = "PASS"

        elif MODAL == "PASS":
            screen.blit(FONT_CARD.render("[" + str(CUR_SSID) + "] Sifresi:", True, (255,255,255)), (mbox.x+40, mbox.top+40))
            inpr = pygame.Rect(mbox.x+40, mbox.top+180, mbox.w-80, 60)
            pygame.draw.rect(screen, (31, 41, 55), inpr)
            pygame.draw.rect(screen, (59, 130, 246), inpr, 2)
            pmask = "*"*len(PASS_INPUT)
            screen.blit(FONT_CARD.render(pmask if pmask else "Klavyeyle sifreyi yazip Enter'a basin...", True, (255,255,255) if pmask else (148, 163, 184)), (inpr.x+20, inpr.y+15))

        elif MODAL == "BT":
            screen.blit(FONT_CARD.render("Bulunan Bluetooth Cihazlar", True, (255,255,255)), (mbox.x+40, mbox.top+30))
            if not BT_LIST: screen.blit(FONT_TEXT.render("Cihaz bulunamadi. Klavyenizi eslestirme moduna alin.", True, (148, 163, 184)), (mbox.x+40, mbox.top+120))
            for idx, (mac, name) in enumerate(BT_LIST[:5]):
                ir = pygame.Rect(mbox.x+40, mbox.top+90+idx*80, mbox.w-80, 65)
                pygame.draw.rect(screen, (30, 41, 59) if ir.collidepoint(mpos) else (17, 24, 39), ir)
                screen.blit(FONT_TEXT.render(name, True, (255,255,255)), (ir.x+15, ir.y+10))
                screen.blit(FONT_TEXT.render(mac, True, (148, 163, 184)), (ir.x+15, ir.y+36))
                pr = pygame.Rect(ir.right-120, ir.y+12, 100, 40)
                pygame.draw.rect(screen, (37, 99, 235), pr)
                screen.blit(FONT_TEXT.render("Eslestir", True, (255,255,255)), (pr.x+15, pr.y+10))
                if any(e.type == pygame.MOUSEBUTTONDOWN and pr.collidepoint(mpos) for e in events):
                    subprocess.run("echo -e 'trust " + str(mac) + "\\npair " + str(mac) + "\\nconnect " + str(mac) + "\\n' | bluetoothctl", shell=True)
                    MODAL = None

    pygame.display.flip()

pygame.quit()
