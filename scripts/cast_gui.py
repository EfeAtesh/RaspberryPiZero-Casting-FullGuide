#!/usr/bin/env python3
import os, sys, time, socket, subprocess, re, math, threading

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"

import pygame

pygame.init()
pygame.font.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Cast Control Center")
clock = pygame.time.Clock()

FONT_TITLE = pygame.font.Font(None, 68)
FONT_SUB = pygame.font.Font(None, 36)
FONT_CARD = pygame.font.Font(None, 34)
FONT_TEXT = pygame.font.Font(None, 28)
FONT_BTN = pygame.font.Font(None, 26)
FONT_PIN = pygame.font.Font(None, 96)

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

# Bluetooth Arka Plan Ajanı ve PIN Yakalayıcı
BT_AUTO_STATUS = "Otomatik Araniyor..."
BT_CONNECTED_DEVICE = None
BT_PIN_PROMPT = None  # Ekranda gosterilecek canli PIN kodu
running = True

def bg_bluetooth_autosearch():
    global BT_AUTO_STATUS, BT_CONNECTED_DEVICE, BT_PIN_PROMPT, running
    try:
        subprocess.run("sudo rfkill unblock bluetooth && sudo systemctl start bluetooth", shell=True)
    except: pass

    # Bluetoothctl etkilesimli ajani baslat
    try:
        bt_proc = subprocess.Popen(
            ["bluetoothctl"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        bt_proc.stdin.write("agent KeyboardOnly\ndefault-agent\npower on\nscan on\n")
        bt_proc.stdin.flush()
    except: return

    attempted_macs = set()

    def stdout_reader():
        global BT_PIN_PROMPT, BT_CONNECTED_DEVICE, BT_AUTO_STATUS
        for line in iter(bt_proc.stdout.readline, ''):
            if not running: break
            # 1. PIN / Passkey Istegi Yakalama
            m_pin = re.search(r"(?:Passkey|PIN code|passkey)[:\s]+([0-9]{4,8})", line, re.IGNORECASE)
            if m_pin:
                BT_PIN_PROMPT = m_pin.group(1)
                BT_AUTO_STATUS = f"PIN Girisi Bekleniyor: {BT_PIN_PROMPT}" if LANG=="TR" else f"Waiting PIN: {BT_PIN_PROMPT}"

            # 2. Otomatik Evet (Confirm) Cevaplama
            if "(yes/no)" in line.lower():
                try:
                    bt_proc.stdin.write("yes\n")
                    bt_proc.stdin.flush()
                except: pass

            # 3. Basarili Eslestirme
            if "Paired: yes" in line or "Connection successful" in line or "Authorize service" in line:
                BT_PIN_PROMPT = None
                BT_AUTO_STATUS = "Baglandi & Aktif!" if LANG=="TR" else "Connected & Active!"

    t_reader = threading.Thread(target=stdout_reader, daemon=True)
    t_reader.start()

    while running:
        try:
            out = subprocess.check_output("bluetoothctl devices 2>/dev/null || true", shell=True).decode(errors="ignore")
            for line in out.strip().split("\n"):
                if "Device" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = " ".join(parts[2:])
                        if mac not in attempted_macs and not BT_CONNECTED_DEVICE:
                            attempted_macs.add(mac)
                            BT_CONNECTED_DEVICE = name
                            BT_AUTO_STATUS = f"Eslestiriliyor: {name[:12]}" if LANG=="TR" else f"Pairing: {name[:12]}"
                            bt_proc.stdin.write(f"pair {mac}\ntrust {mac}\nconnect {mac}\n")
                            bt_proc.stdin.flush()
        except: pass
        time.sleep(3)

bt_thread = threading.Thread(target=bg_bluetooth_autosearch, daemon=True)
bt_thread.start()

def draw_rounded_card(surface, color, rect, radius=40, border_color=(55, 65, 81), border_width=2):
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

def draw_btn(surface, color, rect, text, radius=20, border_color=None, font=FONT_CARD):
    draw_rounded_card(surface, color, rect, radius=radius, border_color=border_color, border_width=2 if border_color else 0)
    txt = font.render(text, True, (255, 255, 255))
    surface.blit(txt, txt.get_rect(center=rect.center))

MODAL = None
WIFI_LIST = []
CUR_SSID = ""
PASS_INPUT = ""
info = get_sys_info()

while running:
    clock.tick(30)
    mpos = pygame.mouse.get_pos()
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT: running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if BT_PIN_PROMPT: BT_PIN_PROMPT = None
                elif MODAL: MODAL = None
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

    # Ust Bilgi ve "Change Language" Butonu
    clock_t = FONT_SUB.render(time.strftime("%H:%M"), True, (148, 163, 184))
    screen.blit(clock_t, (WIDTH - 120, 30))

    lang_r = pygame.Rect(WIDTH - 400, 24, 250, 44)
    draw_btn(screen, (51, 65, 85) if lang_r.collidepoint(mpos) else (30, 41, 59), lang_r, f"Change Language [{LANG}]", radius=14, font=FONT_BTN)
    if any(e.type == pygame.MOUSEBUTTONDOWN and lang_r.collidepoint(mpos) for e in events):
        LANG = "EN" if LANG == "TR" else "TR"
        with open(LANG_FILE, "w") as f: f.write(LANG)

    # Baslik
    t = FONT_TITLE.render("Yayina Hazir" if LANG=="TR" else "Ready to Cast", True, (248, 250, 252))
    screen.blit(t, t.get_rect(center=(WIDTH//2, 110)))
    sub = FONT_SUB.render("Cihaz: " + str(info['host']) + "   |   PIN: 31415926   |   Motor: Player 2 (1080p)", True, (148, 163, 184))
    screen.blit(sub, sub.get_rect(center=(WIDTH//2, 165)))

    # 3 Modern 40dp Kart
    cw, ch = 520, 450
    start_x = (WIDTH - (cw*3 + 120)) // 2

    # Kart 1: Wi-Fi
    c1 = pygame.Rect(start_x, 240, cw, ch)
    c1_hover = c1.collidepoint(mpos)
    draw_rounded_card(screen, (17, 24, 39), c1, radius=40, border_color=(59, 130, 246) if c1_hover else (55, 65, 81), border_width=3 if c1_hover else 2)
    
    screen.blit(FONT_CARD.render("Wi-Fi Agi" if LANG=="TR" else "Wi-Fi Network", True, (255,255,255)), (start_x+40, 275))
    screen.blit(FONT_TEXT.render("Aktif Ag / SSID:", True, (148, 163, 184)), (start_x+40, 345))
    screen.blit(FONT_CARD.render(info["wifi"][:20], True, (56, 189, 248)), (start_x+40, 380))
    screen.blit(FONT_TEXT.render("IP Adresi:", True, (148, 163, 184)), (start_x+40, 445))
    screen.blit(FONT_CARD.render(info["ip"], True, (34, 197, 94)), (start_x+40, 480))

    btn_w = pygame.Rect(start_x+40, 570, cw-80, 60)
    btn_w_hover = btn_w.collidepoint(mpos)
    draw_btn(screen, (59, 130, 246) if btn_w_hover else (37, 99, 235), btn_w, "Aglari Tara / Scan", radius=20)
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_w_hover for e in events):
        WIFI_LIST = scan_wifi()
        MODAL = "WIFI"

    # Kart 2: Bluetooth
    c2 = pygame.Rect(start_x + cw + 60, 240, cw, ch)
    c2_hover = c2.collidepoint(mpos)
    draw_rounded_card(screen, (17, 24, 39), c2, radius=40, border_color=(59, 130, 246) if c2_hover else (55, 65, 81), border_width=3 if c2_hover else 2)

    screen.blit(FONT_CARD.render("Bluetooth Klavye / Fare", True, (255,255,255)), (c2.x+40, 275))
    screen.blit(FONT_TEXT.render("Otomatik Baglanti:", True, (148, 163, 184)), (c2.x+40, 345))
    
    # Canli Durum
    screen.blit(FONT_CARD.render(BT_AUTO_STATUS[:22], True, (34, 197, 94) if "Baglandi" in BT_AUTO_STATUS or "Connected" in BT_AUTO_STATUS else (56, 189, 248)), (c2.x+40, 380))
    screen.blit(FONT_TEXT.render("Klavyenizi eslestirme moduna" if LANG=="TR" else "Put keyboard in pair mode,", True, (148, 163, 184)), (c2.x+40, 445))
    screen.blit(FONT_TEXT.render("alin; PIN otomatik belirecek." if LANG=="TR" else "PIN code will appear live.", True, (148, 163, 184)), (c2.x+40, 475))

    btn_b = pygame.Rect(c2.x+40, 570, cw-80, 60)
    btn_b_hover = btn_b.collidepoint(mpos)
    draw_btn(screen, (16, 185, 129) if "Baglandi" in BT_AUTO_STATUS else (59, 130, 246) if btn_b_hover else (37, 99, 235), btn_b, "✓ Aktif Baglanti" if "Baglandi" in BT_AUTO_STATUS else "Canli Araniyor...", radius=20)

    # Kart 3: Sistem Bilgisi
    c3 = pygame.Rect(start_x + (cw + 60)*2, 240, cw, ch)
    c3_hover = c3.collidepoint(mpos)
    draw_rounded_card(screen, (17, 24, 39), c3, radius=40, border_color=(59, 130, 246) if c3_hover else (55, 65, 81), border_width=3 if c3_hover else 2)

    screen.blit(FONT_CARD.render("Sistem Bilgisi" if LANG=="TR" else "System Health", True, (255,255,255)), (c3.x+40, 275))
    screen.blit(FONT_TEXT.render("CPU Sicaklik / Temp:", True, (148, 163, 184)), (c3.x+40, 345))
    screen.blit(FONT_CARD.render(info["temp"], True, (34, 197, 94)), (c3.x+40, 380))
    screen.blit(FONT_TEXT.render("GPU VRAM:", True, (148, 163, 184)), (c3.x+40, 445))
    screen.blit(FONT_CARD.render("256 MB (VideoCore IV)", True, (56, 189, 248)), (c3.x+40, 480))

    btn_r = pygame.Rect(c3.x+40, 570, cw-80, 60)
    btn_r_hover = btn_r.collidepoint(mpos)
    draw_btn(screen, (225, 29, 72) if btn_r_hover else (185, 28, 28), btn_r, "Yeniden Baslat / Reboot", radius=20)
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_r_hover for e in events):
        subprocess.run("sudo reboot", shell=True)

    # Alt Buton: Yayina Basla (30dp Pill Shape)
    btn_start = pygame.Rect(WIDTH//2 - 270, HEIGHT - 170, 540, 72)
    btn_start_hover = btn_start.collidepoint(mpos)
    draw_btn(screen, (34, 197, 94) if btn_start_hover else (16, 185, 129), btn_start, ">> YAYINA BASLA (START CAST) <<", radius=30)
    if any(e.type == pygame.MOUSEBUTTONDOWN and btn_start_hover for e in events):
        running = False

    # 1. CANLI BLUETOOTH KLAVYE PIN POPUP'I (OTOMATIK EKRANA GELIR)
    if BT_PIN_PROMPT:
        m_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        m_bg.fill((0, 0, 0, 220))
        screen.blit(m_bg, (0, 0))
        
        pinbox = pygame.Rect(WIDTH//2 - 450, HEIGHT//2 - 220, 900, 440)
        draw_rounded_card(screen, (15, 23, 42), pinbox, radius=40, border_color=(34, 197, 94), border_width=3)
        
        # Baslik
        p_title = FONT_CARD.render("KLAVYE ESLISTIRME KODU (PIN)" if LANG=="TR" else "KEYBOARD PAIRING PIN", True, (255, 255, 255))
        screen.blit(p_title, p_title.get_rect(center=(WIDTH//2, pinbox.top + 50)))
        
        # Dev PIN Kutusu
        pkutu = pygame.Rect(WIDTH//2 - 240, pinbox.top + 110, 480, 110)
        draw_rounded_card(screen, (31, 41, 55), pkutu, radius=24, border_color=(56, 189, 248), border_width=2)
        
        # Buyuk PIN Yazisi: Ornek: " 7 3 9 2 0 1 "
        spaced_pin = "  ".join(list(str(BT_PIN_PROMPT)))
        ptxt = FONT_PIN.render(spaced_pin, True, (56, 189, 248))
        screen.blit(ptxt, ptxt.get_rect(center=pkutu.center))
        
        # Talimat
        instr1 = FONT_TEXT.render("Lutfen Bluetooth klavyenizden yukaridaki kodu tuslayip" if LANG=="TR" else "Please type the PIN code above on your Bluetooth keyboard", True, (248, 250, 252))
        instr2 = FONT_CARD.render("ENTER tusuna basin!" if LANG=="TR" else "and press ENTER!", True, (34, 197, 94))
        screen.blit(instr1, instr1.get_rect(center=(WIDTH//2, pinbox.top + 270)))
        screen.blit(instr2, instr2.get_rect(center=(WIDTH//2, pinbox.top + 315)))

        # Iptal Butonu
        btn_cpin = pygame.Rect(WIDTH//2 - 120, pinbox.top + 365, 240, 50)
        draw_btn(screen, (75, 85, 99), btn_cpin, "Iptal / Cancel", radius=14, font=FONT_BTN)
        if any(e.type == pygame.MOUSEBUTTONDOWN and btn_cpin.collidepoint(mpos) for e in events):
            BT_PIN_PROMPT = None

    # 2. Standart Wi-Fi Modali
    elif MODAL == "WIFI":
        m_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        m_bg.fill((0, 0, 0, 200))
        screen.blit(m_bg, (0, 0))
        mbox = pygame.Rect(WIDTH//2 - 420, HEIGHT//2 - 290, 840, 580)
        draw_rounded_card(screen, (15, 23, 42), mbox, radius=40, border_color=(59, 130, 246), border_width=2)

        close_r = pygame.Rect(mbox.right - 65, mbox.top + 20, 42, 42)
        draw_btn(screen, (75, 85, 99), close_r, "X", radius=14)
        if any(e.type == pygame.MOUSEBUTTONDOWN and close_r.collidepoint(mpos) for e in events):
            MODAL = None

        screen.blit(FONT_CARD.render("Wi-Fi Agini Secin", True, (255,255,255)), (mbox.x+50, mbox.top+35))
        if not WIFI_LIST: screen.blit(FONT_TEXT.render("Ag bulunamadi / No networks found.", True, (148, 163, 184)), (mbox.x+50, mbox.top+120))
        for idx, s in enumerate(WIFI_LIST[:6]):
            ir = pygame.Rect(mbox.x+50, mbox.top+95+idx*72, mbox.w-100, 58)
            ir_hover = ir.collidepoint(mpos)
            draw_btn(screen, (30, 41, 59) if ir_hover else (17, 24, 39), ir, s, radius=18)
            if any(e.type == pygame.MOUSEBUTTONDOWN and ir_hover for e in events):
                CUR_SSID = s
                PASS_INPUT = ""
                MODAL = "PASS"

    elif MODAL == "PASS":
        m_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        m_bg.fill((0, 0, 0, 200))
        screen.blit(m_bg, (0, 0))
        mbox = pygame.Rect(WIDTH//2 - 420, HEIGHT//2 - 290, 840, 580)
        draw_rounded_card(screen, (15, 23, 42), mbox, radius=40, border_color=(59, 130, 246), border_width=2)

        close_r = pygame.Rect(mbox.right - 65, mbox.top + 20, 42, 42)
        draw_btn(screen, (75, 85, 99), close_r, "X", radius=14)
        if any(e.type == pygame.MOUSEBUTTONDOWN and close_r.collidepoint(mpos) for e in events):
            MODAL = None

        screen.blit(FONT_CARD.render("[" + str(CUR_SSID) + "] Sifresi:", True, (255,255,255)), (mbox.x+50, mbox.top+45))
        inpr = pygame.Rect(mbox.x+50, mbox.top+180, mbox.w-100, 64)
        draw_rounded_card(screen, (31, 41, 55), inpr, radius=20, border_color=(59, 130, 246), border_width=2)
        pmask = "*"*len(PASS_INPUT)
        screen.blit(FONT_CARD.render(pmask if pmask else "Klavyeyle sifreyi yazip Enter'a basin...", True, (255,255,255) if pmask else (148, 163, 184)), (inpr.x+25, inpr.y+18))

    pygame.display.flip()

running = False
pygame.quit()
