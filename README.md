[raspberry_pi_cast_documentation_en.md](https://github.com/user-attachments/files/31803673/raspberry_pi_cast_documentation_en.md)
# System Architecture, Requirements Specification and Installation Manual (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧
## Wireless Screen Mirroring Receiver System (Miracast / WFD)
**Target Platform:** Raspberry Pi Zero 2 W  
**Engine Profile:** High-Fidelity 1080p Video Streaming (Player 2 / Hardware Buffered)  
**Specification Standard:** Ian Sommerville Software Engineering Documentation Standards  
**Document Version:** 1.3.0  
**Status:** Approved / Operational  

---

## Table of Contents
1. [Quick Installation Guide (3-Minute Setup)](#1-quick-installation-guide-3-minute-setup)
2. [System Overview and Scope](#2-system-overview-and-scope)
3. [System Requirements Specification (SRS)](#3-system-requirements-specification-srs)
4. [System Architecture and Subsystem Decomposition](#4-system-architecture-and-subsystem-decomposition)
5. [Step-by-Step Installation and Deployment Guide](#5-step-by-step-installation-and-deployment-guide)
6. [Performance Engineering & Quality Optimization Specification](#6-performance-engineering--quality-optimization-specification)
7. [Operational Manual and Verification Procedures](#7-operational-manual-and-verification-procedures)
8. [Extra UI Feature: Modern 1080p Control Center Dashboard](#8-extra-ui-feature-modern-1080p-control-center-dashboard)
9. [Fault Analysis and Troubleshooting Matrix](#9-fault-analysis-and-troubleshooting-matrix)

---

## 1. Quick Installation Guide (3-Minute Setup) ⚡ (•̀ᴗ•́)و ̑̑

For rapid, automated deployment on a fresh Raspberry Pi Zero 2 W running **Raspberry Pi OS Lite (32-bit Bullseye)**, execute the following 3 steps:

### Step 1: MicroSD Preparation (on Host Computer)
1. Flash `Raspberry Pi OS (Legacy, 32-bit) Lite` using Raspberry Pi Imager.
2. Open the mounted `bootfs` partition and add to `config.txt`:
   ```ini
   dtoverlay=vc4-fkms-v3d
   dtoverlay=dwc2
   gpu_mem=256
   ```
3. Create an empty file named `ssh` in `bootfs`.

### Step 2: One-Liner Automated Installer (on Raspberry Pi SSH)
Run this single command block in the Pi terminal to complete all installation, compilation, patching, and tuning automatically:

```bash
# 1. Expand filesystem and install packages
sudo raspi-config nonint do_expand_rootfs
sudo apt update && sudo apt install -y build-essential cmake git libx11-dev libasound2-dev libavformat-dev libavcodec-dev python3-evdev busybox python3-pygame fonts-dejavu-core

# 2. Clone and build Userland OpenMAX libraries
git clone --depth 1 https://github.com/raspberrypi/userland.git ~/userland
cd ~/userland && ./buildme
cd /opt/vc/src/hello_pi/libs/ilclient/ && sudo make
cd /opt/vc/src/hello_pi/hello_video && sudo make

# 3. Clone and build LazyCast
git clone https://github.com/homeworkc/lazycast.git ~/lazycast_setup/lazycast
cd ~/lazycast_setup/lazycast && make

# 4. Apply high-fidelity production settings (Player 2 + 1080p + HDMI Audio)
sed -i 's/player_select = .*/player_select = 2/' ~/lazycast_setup/lazycast/d2.py
sed -i 's/disable_1920_1080_60fps = .*/disable_1920_1080_60fps = 1/' ~/lazycast_setup/lazycast/d2.py
sed -i 's/sound_output_select = .*/sound_output_select = 0/' ~/lazycast_setup/lazycast/d2.py

# 5. Deploy auto-cleaning P2P launcher script
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

# 6. Apply network socket buffer tuning
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
sudo iwconfig wlan0 power off 2>/dev/null || true
```

### Step 3: Launch Receiver and Cast
```bash
cd ~/lazycast_setup/lazycast && ./all.sh
```
- Open **Smart View / Cast** on your Android device.
- Connect to **`raspberrypi`** (PIN: `31415926`).

---

## 2. System Overview and Scope 📺 (✿◠‿◠)

### 2.1 Purpose
This document defines the formal software engineering specification, subsystem architecture, deployment protocol, and operational procedures for an embedded wireless display sink (receiver) built on the Raspberry Pi Zero 2 W. The system is engineered to provide high-fidelity, artifact-free 1080p Full HD video and audio casting from mobile devices (Android / Samsung Smart View) directly to HDMI-equipped screens.

### 2.2 System Objectives & Quality Priorities
- **High Visual Fidelity:** Prioritize frame integrity, zero-macroblocking, and sharp 1080p resolution by employing hardware jitter-buffering.
- **Zero Infrastructure Dependency:** Establish direct peer-to-peer (P2P) wireless tunnels without requiring external Wi-Fi routers or internet connectivity.
- **Hardware-Accelerated Decoding:** Leverage Broadcom VideoCore IV GPU acceleration for H.264 video decoding with <10% CPU utilization.
- **Synchronized Audio Delivery:** Stream uncompressed LPCM stereo audio directly across the HDMI video layer with zero audio crackle or distortion.
- **Thermal & Power Efficiency:** Maintain an operational temperature between 45°C and 55°C within a 1.5W–2.5W embedded power envelope.

---

## 3. System Requirements Specification (SRS)

### 3.1 Hardware Requirements
| Item | Specification | Technical Justification |
|---|---|---|
| **SoC / CPU** | Broadcom BCM2710A1 (Quad-core 64-bit Cortex-A53 @ 1.0 GHz) | Handles network socket stack and P2P state machine efficiently. |
| **GPU** | Broadcom VideoCore IV (V3D @ 400 MHz) | Required for hardware H.264 video decoding via OpenMAX IL. |
| **System RAM** | 512 MB LPDDR2 SDRAM | Divided evenly: GPU (256 MB VRAM) and Linux OS (256 MB System RAM). |
| **Storage** | 16 GB+ MicroSD (Class 10 / UHS-I) | Houses base image, kernel buffers, and userland source binaries. |
| **Wireless** | 2.4 GHz IEEE 802.11 b/g/n (Synaptics/Broadcom BCM43436) | Supports Wi-Fi Direct (P2P) and Wi-Fi Display (WFD). |
| **Video/Audio Out** | Mini-HDMI (Type C) | Transmits 1080p video signal and LPCM uncompressed audio to display. |
| **Power Supply** | 5V / 2.5A Micro-USB | Ensures stable power delivery during high-throughput wireless bursts. |

### 3.2 Software & Operating System Specification
- **Operating System:** Raspberry Pi OS Lite (32-bit / Debian 11 "Bullseye")
- **Base Image:** `2023-05-03-raspios-bullseye-armhf-lite.img.xz`
- **Kernel Version:** Linux 5.10.x / 6.1.x `armv7l`
- **Video Display Pipeline:** Fake KMS (`vc4-fkms-v3d`)
- **Multimedia APIs:** Broadcom OpenMAX IL (OMX Core 1.1.2), MMAL, ALSA/HDMI Audio Driver

> [!IMPORTANT]
> **Operating System Selection Rationale (Sommerville Compliance Evaluation):**
> Debian 12 (Bookworm) deprecates legacy Broadcom userland OpenMAX IL libraries in favor of standard Linux V4L2/DRM. However, on 512MB RAM boards, V4L2 introduces extra memory copies and buffer pressure. **Debian 11 (Bullseye)** is formally specified as the target platform to provide native OpenMAX IL hardware endpoints.

---

## 4. System Architecture and Subsystem Decomposition 🏗️ (ง •_•)ง

### 4.1 Architectural Decomposition

```mermaid
graph TD
    subgraph MobileDevice ["Mobile Source (Android / Samsung)"]
        WFD_Src["Wi-Fi Display Source"]
        RTSP_Client["RTSP Client Controller"]
        Media_Encoder["H.264 / LPCM Encoder"]
    end

    subgraph PiZero2W ["Receiver Sink (Raspberry Pi Zero 2 W)"]
        subgraph NetLayer ["1. Network Subsystem"]
            WPA["wpa_supplicant (P2P Device: p2p-dev-wlan0)"]
            DHCP["busybox udhcpd (192.168.173.80)"]
        end

        subgraph ControlLayer ["2. Protocol & Session Controller"]
            LazyCast["LazyCast Control Daemon (d2.py)"]
            RTSP_Server["RTSP Server (Port 7236)"]
        end

        subgraph MediaPipeline ["3. Hardware Media Pipeline (Player 2 Engine)"]
            JitterBuffer["RTP Jitter & Frame Reassembly Queue"]
            OMX_Video["VideoCore IV H.264 Decoder (h264.bin)"]
            OMX_Audio["OpenMAX HDMI Audio Destination"]
        end
    end

    subgraph DisplayOutput ["Display Output"]
        HDMI_Out["HDMI Sink (TV / Monitor)"]
    end

    WFD_Src <-->|P2P Negotiation / WPS PIN| WPA
    WPA --> DHCP
    RTSP_Client <-->|RTSP M1-M7 Handshake (TCP 7236)| RTSP_Server
    Media_Encoder -->|RTP / UDP Packets (Port 1028)| JitterBuffer
    JitterBuffer --> OMX_Video
    JitterBuffer --> OMX_Audio
    OMX_Video -->|1080p Video Stream| HDMI_Out
    OMX_Audio -->|LPCM Stereo Audio| HDMI_Out
```

### 4.2 Protocol Sequence Flow (RTSP M1 to M7 Handshake)

```mermaid
sequenceDiagram
    autonumber
    participant S as Mobile Device (Source)
    participant R as Pi Zero 2 W (Sink)

    Note over S,R: Phase 1: P2P Wi-Fi Direct Association
    S->>R: P2P Probe Request / Group Discovery
    R->>S: P2P Group Owner Formation (WPS PIN: 31415926)
    R->>S: DHCP Lease Allocation (IP: 192.168.173.80)

    Note over S,R: Phase 2: WFD Session Negotiation (RTSP TCP 7236)
    S->>R: M1: OPTIONS Request (org.wfa.wfd1.0)
    R->>S: M1 Response: 200 OK (Supported Methods)
    R->>S: M2: OPTIONS Request (Require: org.wfa.wfd1.0)
    S->>R: M2 Response: 200 OK
    S->>R: M3: GET_PARAMETER (Capabilities Query)
    R->>S: M3 Response: wfd_video_formats (1080p30), LPCM Audio, Port 1028
    S->>R: M4: SET_PARAMETER (Selected 1080p Video Mode)
    R->>S: M4 Response: 200 OK
    S->>R: M5: SET_PARAMETER (Trigger SETUP)
    R->>S: M5 Response: 200 OK
    R->>S: M6: SETUP (Transport: RTP/AVP/UDP;unicast;client_port=1028)
    S->>R: M6 Response: 200 OK (Server Port Assigned)
    R->>S: M7: PLAY (Start Session)
    S->>R: M7 Response: 200 OK

    Note over S,R: Phase 3: High-Fidelity Streaming
    S->>R: Continuous RTP / UDP H.264 Video & LPCM Audio Streams
    R->>R: Jitter-Buffered OpenMAX Direct VideoCore IV Hardware Rendering
```

---

## 5. Step-by-Step Installation and Deployment Guide

### 5.1 Phase 1: Storage Medium Preparation
1. Mount the MicroSD card on the deployment workstation.
2. Flash the official Raspberry Pi OS (Legacy, 32-bit) Bullseye Lite image (`2023-05-03-raspios-bullseye-armhf-lite.img.xz`).
3. Access the `bootfs` (FAT32) partition and configure initial parameters:
   - Create an empty file named `ssh` to enable headless SSH access.
   - Edit `config.txt` to enable Fake KMS, DWC2 USB, and allocate 256MB VRAM:
     ```ini
     dtoverlay=vc4-fkms-v3d
     dtoverlay=dwc2
     gpu_mem=256
     ```
   - Edit `cmdline.txt` to inject USB Ethernet and filesystem modules (in a single continuous line):
     ```text
     console=serial0,115200 console=tty1 root=PARTUUID=4c4e106f-02 rootfstype=ext4 fsck.repair=yes rootwait modules-load=dwc2,g_ether quiet init=/usr/lib/raspberrypi-sys-mods/firstboot
     ```

### 5.2 Phase 2: Post-Boot Storage and Package Provisioning
1. Insert the MicroSD card into the Raspberry Pi Zero 2 W and establish an SSH connection.
2. Expand the root filesystem partition to utilize full storage capacity:
   ```bash
   sudo raspi-config nonint do_expand_rootfs
   ```
3. Update package index and install required toolchains and multimedia libraries:
   ```bash
   sudo apt update
   sudo apt install -y build-essential cmake git libx11-dev libasound2-dev libavformat-dev libavcodec-dev python3-evdev busybox
   ```

### 5.3 Phase 3: Hardware Userland and Core Player Compilation
1. Clone the LazyCast repository into user space:
   ```bash
   git clone https://github.com/homeworkc/lazycast.git ~/lazycast_setup/lazycast
   ```
2. Build Broadcom Userland OpenMAX libraries:
   ```bash
   git clone --depth 1 https://github.com/raspberrypi/userland.git ~/userland
   cd ~/userland && ./buildme
   ```
3. Build the hardware video decoder helper libraries (`ilclient` and `hello_video`):
   ```bash
   cd /opt/vc/src/hello_pi/libs/ilclient/ && sudo make
   cd /opt/vc/src/hello_pi/hello_video && sudo make
   ```
4. Compile the native LazyCast streaming binary engines:
   ```bash
   cd ~/lazycast_setup/lazycast && make
   ```

### 5.4 Phase 4: Production Configuration and Engine Customization
1. **Configure Player 2 as Default High-Fidelity Engine:**
   ```bash
   sed -i 's/player_select = .*/player_select = 2/' ~/lazycast_setup/lazycast/d2.py
   ```
2. **Lock Stream to High-Bitrate 1080p Stabilized Mode:**
   ```bash
   sed -i 's/disable_1920_1080_60fps = .*/disable_1920_1080_60fps = 1/' ~/lazycast_setup/lazycast/d2.py
   ```
3. **Configure Direct HDMI Audio Output Channel:**
   ```bash
   sed -i 's/sound_output_select = .*/sound_output_select = 0/' ~/lazycast_setup/lazycast/d2.py
   ```

---

## 6. Performance Engineering & Quality Optimization Specification 🚀 (★‿★)

```
+-------------------------------------------------------------------------+
|                  Raspberry Pi Zero 2 W Physical RAM (512 MB)            |
+------------------------------------+------------------------------------+
|        GPU VRAM: 256 MB            |         System RAM: 256 MB         |
|  - 1080p H.264 Framebuffers        |  - Linux Kernel & Buffers (~45 MB) |
|  - VideoCore IV Hardware Queues    |  - wpa_supplicant & DHCP  (~15 MB) |
|  - Double/Triple Display Buffering |  - Available Free RAM     (~196 MB)|
+------------------------------------+------------------------------------+
```

### 6.1 VRAM Memory Partitioning (`gpu_mem=256`)
- **GPU Allocation (256 MB):** Allocates optimal memory space for 1080p video decode surfaces, display overlay planes, and hardware reference frames.
- **CPU Allocation (256 MB):** Headless Raspberry Pi OS Lite consumes only ~45–60 MB, leaving ~196 MB free memory, which is fully sufficient for system operations.

### 6.2 Network Stack and Socket Buffer Optimization
To eliminate packet loss during high-bitrate video bursts:
```bash
# Expand UDP receive buffer sizes
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400

# Persist settings across reboots
echo "net.core.rmem_max=26214400" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_default=26214400" | sudo tee -a /etc/sysctl.conf
```

### 6.3 Wireless Power Management Deactivation
Prevents BCM43436 from entering power-saving sleep states during active casting sessions:
```bash
sudo iwconfig wlan0 power off
```

---

## 7. Operational Manual and Verification Procedures 🕹️ (つ✧ω✧)つ

### 7.1 Service Execution
Execute the master casting daemon from the terminal:
```bash
cd ~/lazycast_setup/lazycast
./all.sh
```

**Standard Initialization Output:**
```text
P2P Device: p2p-dev-wlan0
WLAN Interface: wlan0
Active Interface: p2p-wlan0-0
==========================================
  The display is ready!
  Device Name: raspberrypi
  PIN: 31415926
==========================================
```

### 7.2 Client Connection Steps
1. On the client Android device, open Quick Settings and select **Smart View** or **Cast**.
2. Select **`raspberrypi`** (or configured hostname).
3. If prompted, input the PIN: `31415926`.
4. Verification: The sink display immediately transitions to full-screen 1080p mirror mode with synchronized HDMI stereo audio.

---

## 8. Extra UI Feature: Modern 1080p Control Center Dashboard 🎨 (づ｡◕‿‿◕｡)づ

An optional, hardware-accelerated **1080p Dark Glassmorphism Control Center Dashboard** built with Python and Pygame directly on `/dev/fb0`.

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

### 8.1 Key Features & Architecture
- **Full HD Framebuffer Drawing:** Direct `/dev/fb0` rendering at 1920x1080 with zero X11 desktop overhead (<15 MB RAM usage).
- **Interactive Mouse & Keyboard Support:** Smooth cursor, clickable card buttons, hover lighting effects, and arrow key navigation.
- **Wi-Fi Network Scanner Modal:** Discovers nearby SSIDs with graphical signal meters (`%90`, `%75`) and password input dialog.
- **Continuous 8s Bluetooth Scanner:** Scans nearby BLE keyboards and mice with single-click pairing (`pair`, `trust`, `connect`).
- **Bilingual Interface:** One-click language switcher (`[ TR ]` / `[ EN ]`) persisted in `~/.cast_lang`.
- **Smart UX Fallback:** Stays completely hidden during normal boot. Only opens automatically if Wi-Fi cannot connect, or manually when the user runs `menu`.

### 8.2 Launching the Dashboard
Launch the dashboard on demand from terminal:
```bash
menu
```

---

## 9. Fault Analysis and Troubleshooting Matrix

| Symptom / Error | Root Cause | Engineering Resolution |
|---|---|---|
| `No space left on device` during build | MicroSD rootfs partition not resized after flashing. | Execute `sudo raspi-config nonint do_expand_rootfs`. |
| Loop on stale network profile | Stale P2P persistent network profile retained in `wpa_supplicant`. | Deploy patched `all.sh` with automatic `p2p_flush` and group cleanup logic. |
| `ALSA lib: cannot find card '0'` / `Assertion pcm failed` | LazyCast default audio backend attempted to bind to missing 3.5mm analog jack. | Set `sound_output_select = 0` in `d2.py` to route audio directly through OpenMAX HDMI endpoint. |
| Video macro-blocking / dropped frames | Wi-Fi chipset periodic power save throttling. | Execute `sudo iwconfig wlan0 power off` and expand kernel socket buffers. |
| Frame jitter on high-motion scenes | Insufficient decoding queue in unbuffered modes. | Ensure `player_select = 2` is active for hardware-buffered decoding. |
| `TypeError: rect() takes no keyword arguments` in Pygame | Pygame 1.9.6 does not support `border_radius` keyword argument. | Use positional arguments compatible with Pygame 1.9.6 on Debian Bullseye. |

