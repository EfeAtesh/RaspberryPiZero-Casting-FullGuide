#!/bin/bash
set -e

echo "=== Raspberry Pi Zero 2 W - Wireless Cast Automated Installer ==="

# 1. Expand Filesystem
sudo raspi-config nonint do_expand_rootfs

# 2. Install Packages
sudo apt update
sudo apt install -y build-essential cmake git libx11-dev libasound2-dev libavformat-dev libavcodec-dev python3-evdev busybox python3-pygame fonts-dejavu-core fbi python3-pil bluez bluez-tools gpm iw

# 3. Build Userland
if [ ! -d "$HOME/userland" ]; then
    git clone --depth 1 https://github.com/raspberrypi/userland.git "$HOME/userland"
    cd "$HOME/userland" && ./buildme
    cd /opt/vc/src/hello_pi/libs/ilclient/ && sudo make
    cd /opt/vc/src/hello_pi/hello_video && sudo make
fi

# 4. Build LazyCast
mkdir -p "$HOME/lazycast_setup"
if [ ! -d "$HOME/lazycast_setup/lazycast" ]; then
    git clone https://github.com/homeworkc/lazycast.git "$HOME/lazycast_setup/lazycast"
fi
cd "$HOME/lazycast_setup/lazycast" && make

# 5. Apply Player 2 Production Settings
sed -i 's/player_select = .*/player_select = 2/' "$HOME/lazycast_setup/lazycast/d2.py"
sed -i 's/disable_1920_1080_60fps = .*/disable_1920_1080_60fps = 1/' "$HOME/lazycast_setup/lazycast/d2.py"
sed -i 's/sound_output_select = .*/sound_output_select = 0/' "$HOME/lazycast_setup/lazycast/d2.py"

# 6. Setup Network & Power Tweaks
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
sudo iwconfig wlan0 power off 2>/dev/null || true

echo "=== Installation Completed Successfully! ==="
echo "Run: cd ~/lazycast_setup/lazycast && ./all.sh"
