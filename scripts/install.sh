#!/bin/bash
set -e

echo "=== Raspberry Pi Zero 2 W - Wireless Cast Automated Installer (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ==="

# 1. Expand Filesystem & Enable Console Autologin
sudo raspi-config nonint do_expand_rootfs
sudo raspi-config nonint do_boot_behaviour B2

# 2. Configure Silent Boot (Hide kernel text & blinking cursor)
sudo sed -i 's/console=tty1/console=tty3 quiet loglevel=3 vt.global_cursor_default=0 logo.nologo/' /boot/cmdline.txt 2>/dev/null || true

# 3. Mask tty1 login output to prevent console overwriting TV
sudo systemctl stop getty@tty1.service 2>/dev/null || true
sudo systemctl disable getty@tty1.service 2>/dev/null || true
sudo systemctl mask getty@tty1.service 2>/dev/null || true

# 4. Install Required Packages
sudo apt update
sudo apt install -y build-essential cmake git libx11-dev libasound2-dev libavformat-dev libavcodec-dev python3-evdev busybox python3-pygame fonts-dejavu-core fbi python3-pil bluez bluez-tools gpm iw

# 5. Build Userland OpenMAX Libraries
if [ ! -d "$HOME/userland" ]; then
    git clone --depth 1 https://github.com/raspberrypi/userland.git "$HOME/userland"
    cd "$HOME/userland" && ./buildme
    cd /opt/vc/src/hello_pi/libs/ilclient/ && sudo make
    cd /opt/vc/src/hello_pi/hello_video && sudo make
fi

# 6. Build LazyCast
mkdir -p "$HOME/lazycast_setup"
if [ ! -d "$HOME/lazycast_setup/lazycast" ]; then
    git clone https://github.com/homeworkc/lazycast.git "$HOME/lazycast_setup/lazycast"
fi
cd "$HOME/lazycast_setup/lazycast" && make

# 7. Apply Production Quality Settings (Player 2 + HDMI Audio + Continuous Stream)
sed -i 's/player_select = .*/player_select = 2/' "$HOME/lazycast_setup/lazycast/d2.py"
sed -i 's/disable_1920_1080_60fps = .*/disable_1920_1080_60fps = 1/' "$HOME/lazycast_setup/lazycast/d2.py"
sed -i 's/sound_output_select = .*/sound_output_select = 0/' "$HOME/lazycast_setup/lazycast/d2.py"

# 8. Deploy Scripts & Assets
cp scripts/boot_splash.py "$HOME/lazycast_setup/lazycast/" 2>/dev/null || true
cp scripts/cast_gui.py "$HOME/lazycast_setup/lazycast/" 2>/dev/null || true
cp scripts/all.sh "$HOME/lazycast_setup/lazycast/" 2>/dev/null || true
chmod +x "$HOME/lazycast_setup/lazycast/"*.sh "$HOME/lazycast_setup/lazycast/"*.py 2>/dev/null || true

# 9. Generate Responsive 40dp Standby Wallpaper
python3 scripts/make_splash.py 2>/dev/null || python3 "$HOME/lazycast_setup/lazycast/scripts/make_splash.py" 2>/dev/null || true

# 10. Setup & Enable Systemd Service
sudo cp scripts/lazycast.service /etc/systemd/system/lazycast.service 2>/dev/null || sudo cp "$HOME/lazycast_setup/lazycast/scripts/lazycast.service" /etc/systemd/system/lazycast.service 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable lazycast.service

# 11. Apply Network & Power Tweaks
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
sudo iwconfig wlan0 power off 2>/dev/null || true

echo "=== Installation Completed Successfully! (•̀ᴗ•́)و ̑̑ ==="
echo "Your Raspberry Pi will now automatically boot with the minimalist Apple loader into the Wireless Display Receiver!"
