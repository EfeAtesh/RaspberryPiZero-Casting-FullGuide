# Sistem Mimarisi, Gereksinim Şartnamesi ve Kurulum Kılavuzu (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧
## Kablosuz Ekran Yansıtma Alıcı Sistemi (Miracast / WFD)
**Hedef Platform:** Raspberry Pi Zero 2 W  
**Motor Profili:** Yüksek Kaliteli 1080p Video Akışı (Player 2 / Donanımsal Tamponlu)  
**Dokümantasyon Standardı:** Ian Sommerville Yazılım Mühendisliği Standartları  
**Doküman Sürümü:** 1.3.0  
**Durum:** Onaylandı / Çalışır Durumda  

---

## İçindekiler
1. [Hızlı Kurulum Kılavuzu (3 Dakikada Kurulum)](#1-hızlı-kurulum-kılavuzu-3-dakikada-kurulum)
2. [Sistem Genel Bakış ve Kapsam](#2-sistem-genel-bakış-ve-kapsam)
3. [Sistem Gereksinim Şartnamesi (SRS)](#3-sistem-gereksinim-şartnamesi-srs)
4. [Sistem Mimarisi ve Alt Sistem Ayrıştırması](#4-sistem-mimarisi-ve-alt-sistem-ayrıştırması)
5. [Adım Adım Kurulum ve Dağıtım Kılavuzu](#5-adım-adım-kurulum-ve-dağıtım-kılavuzu)
6. [Performans Mühendisliği ve Kalite Optimizasyonu](#6-performans-mühendisliği-ve-kalite-optimizasyonu)
7. [Kullanım Kılavuzu ve Doğrulama Prosedürleri](#7-kullanım-kılavuzu-ve-doğrulama-prosedürleri)
8. [Ekstra UI Özelliği: Modern 1080p Kontrol Merkezi Dashboard](#8-ekstra-ui-özelliği-modern-1080p-kontrol-merkezi-dashboard)
9. [Hata Analizi ve Çözüm Matrisi](#9-hata-analizi-ve-çözüm-matrisi)

---

## 1. Hızlı Kurulum Kılavuzu (3 Dakikada Kurulum) ⚡ (•̀ᴗ•́)و ̑̑

Sıfırdan bir Raspberry Pi Zero 2 W üzerinde **Raspberry Pi OS Lite (32-bit Bullseye)** ile kurulumu 3 dakikada tamamlamak için:

### 1. Adım: SD Kart Hazırlığı (Bilgisayarda)
1. Raspberry Pi Imager ile karta `Raspberry Pi OS (Legacy, 32-bit) Lite` yazdırın.
2. `bootfs` bölümünü açıp `config.txt` dosyasına ekleyin:
   ```ini
   dtoverlay=vc4-fkms-v3d
   dtoverlay=dwc2
   gpu_mem=256
   ```
3. `bootfs` içinde boş bir `ssh` dosyası oluşturun.

### 2. Adım: Tek Komutla Otomatik Kurucu (Pi Terminalinde)
Pi'ye SSH ile bağlanıp şu tek komut bloğunu yapıştırıp çalıştırın:

```bash
# 1. Hafızayı genişlet ve paketleri kur
sudo raspi-config nonint do_expand_rootfs
sudo apt update && sudo apt install -y build-essential cmake git libx11-dev libasound2-dev libavformat-dev libavcodec-dev python3-evdev busybox python3-pygame fonts-dejavu-core

# 2. Donanım video sürücülerini derle
git clone --depth 1 https://github.com/raspberrypi/userland.git ~/userland
cd ~/userland && ./buildme
cd /opt/vc/src/hello_pi/libs/ilclient/ && sudo make
cd /opt/vc/src/hello_pi/hello_video && sudo make

# 3. LazyCast'i indir ve derle
git clone https://github.com/homeworkc/lazycast.git ~/lazycast_setup/lazycast
cd ~/lazycast_setup/lazycast && make

# 4. Yüksek kaliteli üretim ayarlarını uygula (Player 2 + 1080p + HDMI Ses)
sed -i 's/player_select = .*/player_select = 2/' ~/lazycast_setup/lazycast/d2.py
sed -i 's/disable_1920_1080_60fps = .*/disable_1920_1080_60fps = 1/' ~/lazycast_setup/lazycast/d2.py
sed -i 's/sound_output_select = .*/sound_output_select = 0/' ~/lazycast_setup/lazycast/d2.py

# 5. Otomatik temizleyen başlatıcı scripti oluştur
cat << 'EOF' > ~/lazycast_setup/lazycast/all.sh
#!/bin/bash
managefrequency=0
LD_LIBRARY_PATH=/opt/vc/lib
export LD_LIBRARY_PATH

while :
do
	p2pdevinterface=$(sudo wpa_cli interface 2>/dev/null | grep -E "p2p-dev" | tail -1)
	[ -z "$p2pdevinterface" ] && p2pdevinterface="p2p-dev-wlan0"
	wlaninterface="wlan0"

	ain="$(sudo wpa_cli interface 2>/dev/null)"
	if [ $(echo "${ain}" | grep -c "p2p-wl") -eq 0 ]; then
		sudo wpa_cli -i$p2pdevinterface p2p_flush >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface p2p_find type=progressive >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface set device_name "$(uname -n)" >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface set device_type 7-0050F204-1 >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface set p2p_go_ht40 1 >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface wfd_subelem_set 0 000600111c44012c >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface wfd_subelem_set 1 0006000000000000 >/dev/null 2>&1
		sudo wpa_cli -i$p2pdevinterface wfd_subelem_set 6 000700000000000000 >/dev/null 2>&1

		while [ $(echo "${ain}" | grep -c "p2p-wl") -lt 1 ]
		do
			sudo wpa_cli -i$p2pdevinterface p2p_group_add >/dev/null 2>&1
			sleep 2
			ain="$(sudo wpa_cli interface 2>/dev/null)"
		done
	fi

	p2pinterface=$(echo "${ain}" | grep "p2p-wl" | grep -v "interface" | head -1)
	sudo ifconfig $p2pinterface 192.168.173.1 netmask 255.255.255.0 up
	printf "start\t192.168.173.80\nend\t192.168.173.80\ninterface\t$p2pinterface\noption\tsubnet\t255.255.255.0\noption\tlease\t10000\n" > udhcpd.conf
	sleep 1
	sudo pkill udhcpd 2>/dev/null
	sudo busybox udhcpd ./udhcpd.conf >/dev/null 2>&1

	echo "=========================================="
	echo "  The display is ready!"
	echo "  Device Name: $(uname -n)"
	echo "  PIN: 31415926"
	echo "=========================================="

	while :
	do
		sudo wpa_cli -i$p2pinterface wps_pin any 31415926 >/dev/null 2>&1
		./d2.py
		ain="$(sudo wpa_cli interface 2>/dev/null)"
		if [ $(echo "${ain}" | grep -c "p2p-wl") -eq 0 ]; then
			break
		fi
		sleep 1
	done
done
EOF
chmod +x ~/lazycast_setup/lazycast/all.sh

# 6. Ağ ve Wi-Fi optimizasyonlarını uygula
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
sudo iwconfig wlan0 power off 2>/dev/null || true
```

### 3. Adım: Alıcıyı Çalıştır ve Bağlan
```bash
cd ~/lazycast_setup/lazycast && ./all.sh
```
- Telefondan **Smart View / Ekranı Yansıt** menüsünden **`raspberrypi`**'yi seçin (PIN: `31415926`).

---

## 1.1 Tak-Çalıştır Kullanım Kılavuzu (Sıfır Yapılandırma) 🔌 (•̀ᴗ•́)و ̑̑

Kurulum sonrasında Raspberry Pi Zero 2 W'yi **hiçbir klavye, fare veya SSH bağlantısı gerektirmeyen**, tıpkı ticari bir Chromecast gibi %100 otonom bir TV dongle'ına dönüştürün.

```
+-----------------------------------------------------------------------------------+
|                     TAK-ÇALIŞTIR YAŞAM DÖNGÜSÜ İŞ AKIŞI                           |
+-----------------------------------------------------------------------------------+
|  1. GÜÇ BAĞLANTISI   2. SESSİZ AÇILIŞ     3. YAYINA HAZIR      4. TEK TIKLA YAYIN |
|  Micro-USB'yi     -> macOS Yükleme     -> 40dp Apple Kart   -> Android/Windows    |
|  TV'ye / Adaptöre    Barı (2.5 sn)        PIN: 31415926        Miracast Yayını    |
+-----------------------------------------------------------------------------------+
```

### Adım 1: Fiziksel Bağlantı (Donanım Kurulumu)
1. **Görüntü ve Ses:** **Mini-HDMI dönüştürücüyü** Pi Zero 2 W'ye takın ve HDMI kablosuyla TV veya monitörünüze bağlayın.
2. **Güç Beslemesi:** **Micro-USB güç kablosunu** Pi'nin `PWR IN` portuna takıp diğer ucunu TV'nin USB girişine (5V / 1A+) ya da standart bir 5V / 2.5A telefon adaptörüne takın.

### Adım 2: Tam Otomatik Başlama (Müdahalesiz)
- Pi fişe takıldığı an **Sessiz Açılış (Silent Boot)** ile log basmadan başlar.
- TV ekranında siyah zemin üzerinde 2.5 saniyelik şık bir **macOS yükleme çubuğu** dolar.
- Ardından doğrudan **Saf Monokrom Apple Bekleme Ekranı (`Hazir / Ready`)** PIN `31415926` ile açılır.

### Adım 3: Anında Yayın Başlatma (Telefon / Tablet / PC)
- **Samsung ve Android Telefonlar:**
  1. Hızlı Ayarlar menüsünden **Smart View** veya **Ekranı Yansıt**'a dokunun.
  2. Listeden **`raspberrypi`** cihazını seçin.
  3. PIN sorarsa **`31415926`** girin.
  4. Telefonunuzun ekranı ve sesi anında tam ekran 1080p kalitesiyle TV'ye yansır.
- **Windows 10 / 11 Bilgisayarlar:**
  1. Klavyeden `Win + K` tuşlarına basarak Yansıt menüsünü açın.
  2. **`raspberrypi`**'yi seçip PIN kodunu girin.

### Adım 4: Otomatik Bekleme Moduna Dönüş
- Yayını bitirmek istediğinizde telefonunuzdan sadece **Bağlantıyı Kes**'e basmanız yeterlidir.
- Pi hiçbir komut veya yeniden başlatma gerekmeden anında **`Hazir / Ready`** bekleme ekranına geri döner ve bir sonraki yayını bekler.

---

### 1.2 Cihazı Tak-Çalıştır Moduna Ayarlama (Teknik Yapılandırma) ⚙️ (•̀ᴗ•́)و ̑̑

Raspberry Pi'nizi fişe takıldığı anda **hiçbir SSH, klavye veya fare gerekmeden %100 otomatik başlayacak** şekilde yapılandırmak için cihaz üzerinde şu 4 adımı bir kez uygulayın:

#### Adım 1: Otomatik Giriş ve Sessiz Açılışı (Silent Boot) Aktif Etme
Tüm Linux kernel loglarını, açılış kayan yazılarını ve yanıp sönen imleci gizler:
```bash
# 1. Otomatik girişi aç (Login sormasını engeller)
sudo raspi-config nonint do_boot_behaviour B2

# 2. cmdline.txt içine sessiz boot parametrelerini ekle
sudo sed -i 's/console=tty1/console=tty3 quiet loglevel=3 vt.global_cursor_default=0 logo.nologo/' /boot/cmdline.txt

# 3. tty1 konsolunu maskele (Komut satırının TV ekranını ezmesini engeller)
sudo systemctl stop getty@tty1.service 2>/dev/null || true
sudo systemctl disable getty@tty1.service 2>/dev/null || true
sudo systemctl mask getty@tty1.service 2>/dev/null || true
```

#### Adım 2: Arka Plan Otomatik Başlatma Servisini (Systemd) Kurma
Pi açıldığı anda LazyCast motorunu ve bekleme ekranını otomatik başlatır:
```bash
sudo bash -c 'cat << "EOF" > /etc/systemd/system/lazycast.service
[Unit]
Description=LazyCast Wireless Display Receiver
After=network.target sound.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/chromecast/lazycast_setup/lazycast
ExecStart=/bin/bash /home/chromecast/lazycast_setup/lazycast/all.sh
Restart=always
RestartSec=2
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
EOF'

# Servisi her açılış için kalıcı olarak etkinleştir
sudo systemctl daemon-reload
sudo systemctl enable lazycast.service
sudo systemctl restart lazycast.service
```

#### Adım 3: Otonom Başlatmayı Test Etme
Pi'yi yeniden başlatarak tak-çalıştır modunu test edin:
```bash
sudo reboot
```
1. Ekran siyah zemin üzerinde **2.5 saniyelik macOS yükleme çubuğuyla** açılır.
2. Ardından doğrudan **Saf Monokrom Bekleme Ekranına (`Hazir / Ready`)** geçer.
3. Telefonundan PIN: **`31415926`** ile anında yayına başla!

---

## 2. Sistem Genel Bakış ve Kapsam 📺 (✿◠‿◠)

### 2.1 Amaç
Bu belge, Raspberry Pi Zero 2 W üzerinde çalışan gömülü bir kablosuz ekran alıcısı (sink) sisteminin yazılım mühendisliği gereksinimlerini, mimarisini, kurulum adımlarını ve kullanım prosedürlerini tanımlar. Sistem, Android mobil cihazlardan (Smart View / Miracast) HDMI ekranlara **kristal netliğinde, takılmasız ve pürüzsüz 1080p Full HD video ve ses** aktarımını hedefler.

### 2.2 Sistem Hedefleri ve Kalite Öncelikleri
- **Yüksek Görüntü Kalitesi:** Önceliği anlık dokunma tepkisinden ziyade pürüzsüz video akışına, sıfır kare kaybına ve 1080p netliğe vermek.
- **Sıfır Altyapı Bağımlılığı:** Harici modem veya internet bağlantısına ihtiyaç duymadan doğrudan Wi-Fi Direct (P2P) tüneli kurmak.
- **Donanımsal Video Çözme:** Broadcom VideoCore IV GPU donanım hızlandırmasını kullanarak işlemciyi (CPU) %10'un altında tutmak.
- **Senkronize HDMI Ses:** Sesi doğrudan HDMI video katmanına LPCM stereo olarak gömerek cızırtısız ve senkronize iletmek.

---

## 3. Sistem Gereksinim Şartnamesi (SRS)

### 3.1 Donanım Bileşenleri ve Malzeme Listesi 🔌 (•̀ᴗ•́)و ̑̑

<p align="center">
  <img src="./assets/hardware_materials.jpg" width="55%" alt="Donanim Malzemeleri" />
</p>

| Bileşen | Önerilen Özellik | Görev ve Fonksiyon |
|---|---|---|
| **Raspberry Pi Zero 2 W** | 4 Çekirdek 64-bit Cortex-A53 @ 1.0 GHz, 512MB RAM | Ana işlemci ve VideoCore IV H.264 donanım çözücü |
| **Micro-USB Güç Kablosu** | 5V / 2.5A destekli kaliteli Micro USB-B kablosu | Yüksek Wi-Fi veri transferinde kararlı güç beslemesi |
| **HDMI Kablosu** | Standart Yüksek Hızlı HDMI kablosu | Görüntü ve LPCM sesi kayıpsız TV'ye aktarır |
| **Mini-HDMI - HDMI Dönüştürücü** | Mini-HDMI (Type-C Erkek) -> Standart HDMI (Dişi) | Pi Zero 2 W çıkışını standart TV kablosuna bağlar |
| **Koruyucu Kutu + Alüminyum Soğutucu** | Metal soğutucu bloklu Zero 2 W kasası (Önerilen) | Pasif ısı dağılımı (45°C - 55°C aralığında tutar) |
| **MicroSD Hafıza Kartı** | En az 8 GB / 16 GB (Class 10 / UHS-I) | İşletim sistemi, tamponlar ve kütüphaneleri barındırır |

| Bileşen | Özellik | Teknik Gerekçe |
|---|---|---|
| **SoC / İşlemci** | Broadcom BCM2710A1 (4 Çekirdek 64-bit Cortex-A53 @ 1.0 GHz) | Ağ yığını ve P2P durum makinesini yönetir. |
| **GPU** | Broadcom VideoCore IV (V3D @ 400 MHz) | OpenMAX IL üzerinden 1080p H.264 donanımsal çözme sağlar. |
| **RAM** | 512 MB LPDDR2 SDRAM | GPU (256 MB VRAM) ve Linux OS (256 MB) olarak bölünmüştür. |
| **Depolama** | 16 GB+ MicroSD (Class 10) | İşletim sistemi ve kütüphaneleri barındırır. |
| **Kablosuz Çip** | 2.4 GHz 802.11 b/g/n (BCM43436) | Wi-Fi Direct (P2P) ve WFD protokolünü destekler. |
| **Görüntü/Ses Çıkışı** | Mini-HDMI (Type C) | TV'ye 1080p video ve LPCM uncompressed ses taşır. |

### 3.2 İşletim Sistemi Şartnamesi
- **İşletim Sistemi:** Raspberry Pi OS Lite (32-bit / Debian 11 Bullseye)
- **İmaj Dosyası:** `2023-05-03-raspios-bullseye-armhf-lite.img.xz`
- **Video Sürücüsü:** Fake KMS (`vc4-fkms-v3d`)
- **Çoklu Ortam API'si:** Broadcom OpenMAX IL (OMX Core 1.1.2)

---

## 4. Sistem Mimarisi ve Alt Sistem Ayrıştırması 🏗️ (ง •_•)ง

```mermaid
graph TD
    subgraph MobileDevice ["Mobil Cihaz (Android / Samsung)"]
        WFD_Src["Wi-Fi Display Kaynağı"]
        RTSP_Client["RTSP İstemci Kontrolcüsü"]
        Media_Encoder["H.264 / LPCM Kodlayıcı"]
    end

    subgraph PiZero2W ["Alıcı Cihaz (Raspberry Pi Zero 2 W)"]
        subgraph NetLayer ["1. Ağ Katmanı"]
            WPA["wpa_supplicant (P2P Arabirimi: p2p-dev-wlan0)"]
            DHCP["busybox udhcpd (IP: 192.168.173.80)"]
        end

        subgraph ControlLayer ["2. Protokol Kontrol Katmanı"]
            LazyCast["LazyCast Daemon (d2.py)"]
            RTSP_Server["RTSP Sunucusu (TCP 7236)"]
        end

        subgraph MediaPipeline ["3. Donanımsal Medya Boru Hattı (Player 2)"]
            JitterBuffer["RTP Tampon ve Kare Birleştirme Kuyruğu"]
            OMX_Video["VideoCore IV H.264 Çözücü (h264.bin)"]
            OMX_Audio["OpenMAX HDMI Ses Çıkış Uç Noktası"]
        end
    end

    subgraph DisplayOutput ["Görüntü Çıkışı"]
        HDMI_Out["HDMI Ekran (TV / Monitör)"]
    end

    WFD_Src ---|"P2P Eslesme / PIN: 31415926"| WPA
    WPA --> DHCP
    RTSP_Client ---|"RTSP M1-M7 El Sikismasi"| RTSP_Server
    Media_Encoder -->|"RTP / UDP Paketleri"| JitterBuffer
    JitterBuffer --> OMX_Video
    JitterBuffer --> OMX_Audio
    OMX_Video -->|"1080p Video"| HDMI_Out
    OMX_Audio -->|"LPCM Stereo Ses"| HDMI_Out
```

---


### 4.2 Protokol Akış Şeması (RTSP M1 - M7 El Sıkışması)

```mermaid
sequenceDiagram
    autonumber
    participant S as Mobil Cihaz (Kaynak)
    participant R as Pi Zero 2 W (Alıcı)

    Note over S,R: Aşama 1: P2P Wi-Fi Direct Eşleşmesi
    S->>R: P2P Probe Request / Grup Keşfi
    R->>S: P2P Group Owner Oluşturma (WPS PIN: 31415926)
    R->>S: DHCP IP Dağıtımı (IP: 192.168.173.80)

    Note over S,R: Aşama 2: WFD Oturum Anlaşması (RTSP TCP 7236)
    S->>R: M1: OPTIONS İsteği (org.wfa.wfd1.0)
    R->>S: M1 Cevabı: 200 OK (Desteklenen Metotlar)
    R->>S: M2: OPTIONS İsteği (Require: org.wfa.wfd1.0)
    S->>R: M2 Cevabı: 200 OK
    S->>R: M3: GET_PARAMETER (Yetenek Sorgulama)
    R->>S: M3 Cevabı: wfd_video_formats (1080p30), LPCM Audio, Port 1028
    S->>R: M4: SET_PARAMETER (Seçilen 1080p Modu)
    R->>S: M4 Cevabı: 200 OK
    S->>R: M5: SET_PARAMETER (SETUP Tetikleme)
    R->>S: M5 Cevabı: 200 OK
    R->>S: M6: SETUP (Transport: RTP/AVP/UDP, unicast, client_port=1028)
    S->>R: M6 Cevabı: 200 OK (Sunucu Portu Atandı)
    R->>S: M7: PLAY (Akışı Başlat)
    S->>R: M7 Cevabı: 200 OK

    Note over S,R: Aşama 3: Yüksek Kaliteli Video/Ses Akışı
    S->>R: Kesintisiz RTP / UDP H.264 Video ve LPCM Ses Paketleri
    R->>R: Jitter Tamponlu VideoCore IV Doğrudan Donanım Çözme
```

---

## 5. Adım Adım Kurulum ve Dağıtım Kılavuzu

### 5.1 Aşama 1: SD Kart Hazırlığı
1. MicroSD kartı bilgisayara takın ve Raspberry Pi Imager ile `Raspberry Pi OS (Legacy, 32-bit) Lite (Bullseye)` yazdırın.
2. `bootfs` bölümünü açıp:
   - Boş bir `ssh` dosyası oluşturun.
   - `config.txt` içine ekleyin:
     ```ini
     dtoverlay=vc4-fkms-v3d
     dtoverlay=dwc2
     gpu_mem=256
     ```
   - `cmdline.txt` dosyasında `rootwait` sonrasına `modules-load=dwc2,g_ether` ekleyin.

### 5.2 Aşama 2: Sistem Paketleri ve Hafıza Genişletme
1. Pi'yi başlatıp SSH ile bağlanın ve depolamayı genişletin:
   ```bash
   sudo raspi-config nonint do_expand_rootfs
   ```
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   sudo apt update
   sudo apt install -y build-essential cmake git libx11-dev libasound2-dev libavformat-dev libavcodec-dev python3-evdev busybox
   ```

### 5.3 Aşama 3: Donanım Sürücüleri ve Motor Derlemesi
1. Lazycast ve Userland depolarını derleyin:
   ```bash
   git clone https://github.com/homeworkc/lazycast.git ~/lazycast_setup/lazycast
   git clone --depth 1 https://github.com/raspberrypi/userland.git ~/userland
   cd ~/userland && ./buildme
   cd /opt/vc/src/hello_pi/libs/ilclient/ && sudo make
   cd /opt/vc/src/hello_pi/hello_video && sudo make
   cd ~/lazycast_setup/lazycast && make
   ```

### 5.4 Aşama 4: Üretim Yapılandırması (Player 2 Kalite Modu)
1. **Player 2 ve HDMI Ses Ayarlarını Sabitleyin:**
   ```bash
   sed -i 's/player_select = .*/player_select = 2/' ~/lazycast_setup/lazycast/d2.py
   sed -i 's/disable_1920_1080_60fps = .*/disable_1920_1080_60fps = 1/' ~/lazycast_setup/lazycast/d2.py
   sed -i 's/sound_output_select = .*/sound_output_select = 0/' ~/lazycast_setup/lazycast/d2.py
   ```

---

## 6. Performans Mühendisliği ve Kalite Optimizasyonu 🚀 (★‿★)

### 6.1 VRAM Dağılımı (`gpu_mem=256`)
- **GPU Belleği (256 MB):** 1080p video kare tamponları, çift/üçlü tamponlama ve donanımsal renk uzayı dönüşümü için ayrılmıştır.
- **Sistem RAM (256 MB):** Grafik arayüzü olmayan Lite sistem boşta ~45–60 MB harcadığından geriye kalan ~196 MB boş RAM sistem için tam verim sağlar.

### 6.2 Ağ Soket Tamponları ve Wi-Fi Güç Yönetimi
```bash
# Paket düşmelerini önlemek için UDP soket tamponunu genişletin
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400

# Wi-Fi çipinin uyku moduna geçerek kare atlamasını önleyin
sudo iwconfig wlan0 power off
```

---

## 7. Kullanım Kılavuzu ve Doğrulama Prosedürleri 🕹️ (つ✧ω✧)つ

### 7.1 Alıcıyı Başlatma
```bash
cd ~/lazycast_setup/lazycast
./all.sh
```

### 7.2 Bağlanma Adımları
1. Android cihazınızda **Smart View** veya **Ekranı Yansıt** menüsünü açın.
2. Listeden **`raspberrypi`** cihazını seçin.
3. PIN sorarsa **`31415926`** girin.
4. Görüntü tam ekran olarak TV'ye aktarılacaktır.

### 7.3 Canlı TV Ekranı Doğrulaması ve HDMI Ses Testi (つ✧ω✧)つ

<p align="center">
  <img src="./assets/live_tv_standby_test.jpg" width="65%" alt="Canli TV Bekleme Ekrani Dogrulamasi" />
</p>

> [!NOTE]
> **Canlı Test ve Çalışma Doğrulaması:**
> - **Görüntü Hattı:** 1080p Full HD bekleme ekranı 40dp yuvarlatılmış kavisler ve büyük net vektör fontlarla ekrana yansıtıldı.
> - **Ses Hattı:** Ses sinyali HDMI kablosu üzerinden doğrudan LPCM stereo formatında aktarılmakta (`sound_output_select = 0`), harici ses kartı ihtiyacı olmadan kristal netliğinde çalışmaktadır.
> - **P2P Yayını:** Wi-Fi Direct sinyali `p2p-dev-wlan0` üzerinden PIN `31415926` ile yayına hazır durumdadır.

1. Android cihazınızda **Smart View** veya **Ekranı Yansıt** menüsünü açın.
2. Listeden **`raspberrypi`** cihazını seçin.
3. PIN sorarsa **`31415926`** girin.
4. Görüntü tam ekran 1080p olarak TV'ye aktarılacaktır.

---

## 8. Ekstra UI Özelliği: Modern 1080p Kontrol Merkezi Dashboard 🎨 (づ｡◕‿‿◕｡)づ

### 📺 Canlı Arayüz Galerisi (Modern Dashboard vs. Klasik Menü)

<p align="center">
  <img src="./assets/dashboard_tv_screenshot.jpg" width="48%" alt="Modern 1080p Pygame UI" />
  <img src="./assets/classic_tui_screenshot.png" width="48%" alt="Klasik TUI Menüsü" />
</p>

| Özellik | Modern 1080p Pygame Paneli (`menu`) | Klasik TUI Menüsü (`classic-menu`) |
|:---|:---:|:---:|
| **Görsel Motor** | Doğrudan `/dev/fb0` Framebuffer Donanım Çizimi | Hafif `ncurses` (Whiptail) |
| **Kart Tasarımı** | **40dp Kavisli Kartlar**, Apple TV Koyu Cam Efekti | Sade Retro Metin Menüsü |
| **Bluetooth Eşleşme** | **Otomatik Arka Plan Avcısı & Canlı PIN Penceresi** | Adım Adım Metin Sihirbazı |
| **Giriş Desteği** | Tam Fare İmleci ve Klavye Desteği | Klavye Yön Tuşları ve Fare |
| **Dil Desteği** | Anlık Tek Tıkla `[TR]` / `[EN]` Geçişi | Türkçe / İngilizce Seçim Penceresi |

---


---


---

### 📺 Arayüz Karşılaştırması: Modern Dashboard vs. Klasik Menü

| Modern 1080p Pygame Arayüzü (`menu`) | Klasik Hafif TUI Menüsü (`classic-menu`) |
|:---:|:---:|
| ![Modern UI](assets/dashboard_tv_screenshot.jpg) | ![Classic UI](assets/classic_tui_screenshot.png) |
| *40dp kavisli kartlar, canlı donanım takibi, koyu cam efekti ve fare/klavye destekli 1080p modern panel.* | *Düşük kaynak tüketen, hızlı ve pratik ncurses tabanlı klasik metin menüsü.* |

- **Modern Paneli Başlat:** `menu` (veya `sudo python3 scripts/cast_gui.py`)
- **Klasik Menüyü Başlat:** `classic-menu` (veya `bash scripts/classic_menu.sh`)




*Raspberry Pi Zero 2 W üzerinde çalışan 40dp kavisli kartlar, canlı CPU sıcaklık ve VRAM takibi, Bluetooth ve Wi-Fi yöneticili Koyu Cam Efektli (Dark Glassmorphism) Modern Arayüz.*


İsteğe bağlı olarak kullanılabilen, doğrudan `/dev/fb0` üzerine çizilen donanım hızlandırmalı, koyu temalı **1080p Dark Glassmorphism Kontrol Merkezi Dashboard'u** (Python / Pygame):

```
+-------------------------------------------------------------------------------+
|                       📺 WIRELESS DISPLAY DASHBOARD                           |
|  [ 🌐 TR | EN ]                                               [ 21:55 ]       |
+-------------------------------------------------------------------------------+
|                                                                               |
|               ● WIRELESS DISPLAY RECEIVER                                     |
|               Yayına Hazır • Smart View ile Bağlanın                          |
|                                                                               |
|     +--------------------+   +--------------------+   +--------------------+  |
|     |  📶 Wi-Fi Ağı      |   |  ⌨️ 🖱️ Bluetooth   |   |  ℹ️ Sistem Durumu  |  |
|     |                    |   |                    |   |                    |  |
|     |  Ev-Fiber-5G       |   |  Klavye & Fare     |   |  CPU: 46°C         |  |
|     |  IP: 192.168.1.105 |   |  Eşleştirme        |   |  VRAM: 256 MB      |  |
|     |                    |   |                    |   |  Player 2 (1080p)  |  |
|     |  [ Ağları Tara ]   |   |  [ Cihaz Tara ]    |   |  [ Yeniden Başlat] |  |
|     +--------------------+   +--------------------+   +--------------------+  |
|                                                                               |
|               [ ▶ YAYINA BAŞLA (STANDBY MODUNA GEÇ) ]                         |
+-------------------------------------------------------------------------------+
```

### 8.1 Temel Özellikler
- **Doğrudan Framebuffer Çizimi:** Masaüstü ortamı olmadan `/dev/fb0` üzerinden 1920x1080 çizim yapar (<15 MB RAM tüketir).
- **Fare ve Klavye Desteği:** Fare imleciyle tıklanabilir kartlar, neon parlama efektleri ve ok tuşlarıyla gezinme.
- **Wi-Fi Tarama Penceresi:** Çevredeki ağları sinyal çubuklarıyla (%90, %75) listeler ve şifre giriş penceresi sunar.
- **Canlı 8s Bluetooth Tarayıcı:** BLE klavye ve fareleri tarayıp tek tıkla eşleştirir (`pair`, `trust`, `connect`).
- **Çift Dil Desteği:** Sağ üstteki butonla tek tıkla **Türkçe / English** geçişi sağlar.
- **Akıllı Açılış:** Normal açılışta tamamen gizlidir (%100 sessiz Tak-Çalıştır). Yalnızca Wi-Fi bağlanamazsa veya kullanıcı `menu` yazarsa açılır.

### 8.2 Dashboard'u Başlatma
Terminalden istediğiniz zaman çalıştırmak için:
```bash
menu
```

---

## 9. Hata Analizi ve Çözüm Matrisi

| Belirti / Hata | Kök Neden | Çözüm |
|---|---|---|
| Derleme sırasında `No space left on device` | SD kart ana bölümü genişletilmemiş. | `sudo raspi-config nonint do_expand_rootfs` çalıştırın. |
| Başlatıcıda eski oturuma takılma | `wpa_supplicant` içinde eski P2P profili kalması. | Otomatik temizleyen güncel `all.sh` scriptini kullanın. |
| `ALSA lib: cannot find card '0'` çökmesi | Zero 2 W'de 3.5mm jak olmaması nedeniyle ALSA hatası. | `d2.py` dosyasında `sound_output_select = 0` (HDMI) yapın. |
| Yayında takılma / kare atlaması | Wi-Fi güç tasarrufunun açık olması. | `sudo iwconfig wlan0 power off` komutunu uygulayın. |
| Pygame `TypeError: rect() takes no keyword arguments` | Pygame 1.9.6 sürümünün `border_radius` parametresini desteklememesi. | Pygame 1.9.6 uyumlu pozisyonel parametreli scripti kullanın. |
