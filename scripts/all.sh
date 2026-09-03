#!/bin/bash
managefrequency=0
LD_LIBRARY_PATH=/opt/vc/lib
export LD_LIBRARY_PATH

# Ilk acilista bekleme ekranini ekrana bas
sudo fbi -d /dev/fb0 -T 1 -noverbose -a /home/chromecast/lazycast_setup/lazycast/splash.png >/dev/null 2>&1

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

	while :
	do
		sudo wpa_cli -i$p2pinterface wps_pin any 31415926 >/dev/null 2>&1
		./d2.py
		
		# Yayin bittiginde ekrani aninda bekleme resmine geri dondur
		sudo fbi -d /dev/fb0 -T 1 -noverbose -a /home/chromecast/lazycast_setup/lazycast/splash.png >/dev/null 2>&1

		ain="$(sudo wpa_cli interface 2>/dev/null)"
		if [ $(echo "${ain}" | grep -c "p2p-wl") -eq 0 ]; then
			break
		fi
		sleep 1
	done
done
