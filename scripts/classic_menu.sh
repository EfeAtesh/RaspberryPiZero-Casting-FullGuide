#!/bin/bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export NCURSES_NO_UTF8_ACS=1

LANG_FILE="$HOME/.cast_lang"
[ -f "$LANG_FILE" ] && LANG_CODE=$(cat "$LANG_FILE") || LANG_CODE="TR"
sudo systemctl start gpm >/dev/null 2>&1

set_language() {
    if [ "$LANG_CODE" == "TR" ]; then
        T_TITLE="RASPBERRY PI CAST - KONTROL MERKEZI"
        T_SUB="Lutfen bir islem secin (Klavye veya Fare ile):"
        T_OPT1="[Wi-Fi] Aglari Tara ve Baglan"
        T_OPT2="[Bluetooth] Klavye / Fare Eslestir"
        T_OPT3="[Dil / Language] Turkce / English"
        T_OPT4="[Sistem] Durum Bilgisi (IP, Temp, VRAM)"
        T_OPT5="[Yayin] Bekleme Ekranina Don"
        T_OPT6="[Guc] Sistemi Yeniden Baslat"
        T_SCAN_WIFI="Cevredeki kablosuz aglar taraniyor..."
        T_NO_WIFI="Hicbir Wi-Fi agi bulunamadi."
        T_WIFI_TITLE="Wi-Fi Ag Secimi"
        T_PASS_TITLE="Wi-Fi Sifresi"
        T_CONNECTING="Wi-Fi agina baglaniliyor..."
        T_SUCCESS="Basarili!"
        T_BT_SCAN="Klavyenizi/Farenizi eslestirme moduna alin. Taraniyor..."
        T_NO_BT="Hicbir Bluetooth cihazi bulunamadi."
        T_BT_PAIRING="Cihaz eslestiriliyor ve baglaniliyor..."
        T_BT_SUCCESS="Bluetooth cihazi basariyla baglandi!"
        T_STATUS_TITLE="Sistem Durumu"
    else
        T_TITLE="RASPBERRY PI CAST - CONTROL CENTER"
        T_SUB="Please select an option (Using Keyboard or Mouse):"
        T_OPT1="[Wi-Fi] Scan and Connect Network"
        T_OPT2="[Bluetooth] Pair Keyboard / Mouse"
        T_OPT3="[Language / Dil] English / Turkce"
        T_OPT4="[System] Status (IP, Temp, VRAM)"
        T_OPT5="[Cast] Return to Standby Screen"
        T_OPT6="[Power] Reboot System"
        T_SCAN_WIFI="Scanning nearby Wi-Fi networks..."
        T_NO_WIFI="No Wi-Fi networks found."
        T_WIFI_TITLE="Wi-Fi Network Selection"
        T_PASS_TITLE="Wi-Fi Password"
        T_CONNECTING="Connecting to Wi-Fi network..."
        T_SUCCESS="Success!"
        T_BT_SCAN="Put Keyboard/Mouse in pairing mode. Scanning..."
        T_NO_BT="No Bluetooth devices found."
        T_BT_PAIRING="Pairing and connecting device..."
        T_BT_SUCCESS="Bluetooth device connected successfully!"
        T_STATUS_TITLE="System Status"
    fi
}

change_language_dialog() {
    L_CHOICE=$(whiptail --title "Language / Dil" --menu "Secim Yapin / Select Language:" 12 55 2 "TR" "Turkce (Turkish)" "EN" "English" 3>&1 1>&2 2>&3)
    if [ -n "$L_CHOICE" ]; then
        LANG_CODE="$L_CHOICE"
        echo "$LANG_CODE" > "$LANG_FILE"
        set_language
    fi
}

main_menu() {
    while true; do
        set_language
        CHOICE=$(whiptail --title "$T_TITLE" --menu "$T_SUB" 18 68 6 "1" "$T_OPT1" "2" "$T_OPT2" "3" "$T_OPT3" "4" "$T_OPT4" "5" "$T_OPT5" "6" "$T_OPT6" 3>&1 1>&2 2>&3)
        case $CHOICE in
            1) wifi_manager ;;
            2) bluetooth_manager ;;
            3) change_language_dialog ;;
            4) system_status ;;
            5) return_to_cast ;;
            6) sudo reboot ;;
            *) exit 0 ;;
        esac
    done
}

wifi_manager() {
    whiptail --title "Wi-Fi" --infobox "$T_SCAN_WIFI" 7 60
    sudo iwlist wlan0 scan 2>/dev/null | awk -F: '/Quality=/ {split($2,a," "); q=a[1]; sub("/.*","",q); qual=int(q*100/70)} /ESSID:/ {gsub("\"","",$2); if($2!="") print $2 "|" qual "%"}' | sort -u > /tmp/wifiscan.txt
    if [ ! -s /tmp/wifiscan.txt ]; then
        whiptail --title "Wi-Fi" --msgbox "$T_NO_WIFI" 8 45
        return
    fi
    menu_list=()
    while IFS="|" read -r ssid qual; do
        menu_list+=("$ssid" "Sinyal: $qual")
    done < /tmp/wifiscan.txt
    SELECTED_SSID=$(whiptail --title "$T_WIFI_TITLE" --menu "SSID Secin:" 18 65 8 "${menu_list[@]}" 3>&1 1>&2 2>&3)
    if [ -n "$SELECTED_SSID" ]; then
        PASS=$(whiptail --title "$T_PASS_TITLE" --passwordbox "[$SELECTED_SSID] Sifresi:" 10 55 3>&1 1>&2 2>&3)
        if [ -n "$PASS" ]; then
            whiptail --title "Wi-Fi" --infobox "$T_CONNECTING" 7 50
            sudo wpa_cli -i wlan0 add_network >/dev/null 2>&1
            NID=$(sudo wpa_cli -i wlan0 list_networks | tail -1 | awk '{print $1}')
            sudo wpa_cli -i wlan0 set_network $NID ssid "\"$SELECTED_SSID\"" >/dev/null 2>&1
            sudo wpa_cli -i wlan0 set_network $NID psk "\"$PASS\"" >/dev/null 2>&1
            sudo wpa_cli -i wlan0 enable_network $NID >/dev/null 2>&1
            sudo wpa_cli -i wlan0 save_config >/dev/null 2>&1
            sleep 4
            NEW_IP=$(hostname -I | awk '{print $1}')
            whiptail --title "$T_SUCCESS" --msgbox "Baglandi! IP: ${NEW_IP:-Yok}" 10 50
        fi
    fi
}

bluetooth_manager() {
    whiptail --title "Bluetooth" --infobox "$T_BT_SCAN" 8 60
    sudo systemctl start bluetooth
    echo -e "power on\nscan on\n" | bluetoothctl >/dev/null 2>&1 &
    SCAN_PID=$!
    sleep 7
    kill $SCAN_PID 2>/dev/null
    bluetoothctl devices | grep -E "Device" | awk '{$1=""; mac=$2; $2=""; print mac "|" substr($0,2)}' > /tmp/btdevices.txt
    if [ ! -s /tmp/btdevices.txt ]; then
        whiptail --title "Bluetooth" --msgbox "$T_NO_BT" 10 55
        return
    fi
    bt_menu=()
    while IFS="|" read -r mac name; do
        [ -z "$name" ] && name="Bluetooth Cihaz"
        bt_menu+=("$mac" "$name")
    done < /tmp/btdevices.txt
    CHOSEN_MAC=$(whiptail --title "Bluetooth Cihazlar" --menu "Cihaz Secin:" 18 65 8 "${bt_menu[@]}" 3>&1 1>&2 2>&3)
    if [ -n "$CHOSEN_MAC" ]; then
        whiptail --title "Bluetooth" --infobox "$T_BT_PAIRING" 7 60
        echo -e "trust $CHOSEN_MAC\npair $CHOSEN_MAC\nconnect $CHOSEN_MAC\n" | bluetoothctl >/dev/null 2>&1
        sleep 3
        whiptail --title "$T_SUCCESS" --msgbox "$T_BT_SUCCESS" 9 55
    fi
}

system_status() {
    TEMP=$(vcgencmd measure_temp | cut -d= -f2)
    IP=$(hostname -I | awk '{print $1}')
    VRAM=$(vcgencmd get_mem gpu | cut -d= -f2)
    CUR_WIFI=$(sudo iwgetid -r 2>/dev/null || echo "Bagli Degil")
    whiptail --title "$T_STATUS_TITLE" --msgbox "Cihaz Adi: $(uname -n)\nAktif IP: ${IP:-Yok}\nBagli Wi-Fi: $CUR_WIFI\nGPU VRAM: $VRAM\nSicaklik: $TEMP\nDurum: Yayina Hazir (Player 2 / 1080p)" 14 55
}

return_to_cast() {
    sudo fbi -d /dev/fb0 -T 1 -noverbose -a ~/lazycast_setup/lazycast/splash.png >/dev/null 2>&1
    clear
    exit 0
}

main_menu
