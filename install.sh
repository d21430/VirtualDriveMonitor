#!/bin/bash
apt-get install python3 python3-pip -y
apt-get install hwinfo -y
apt-get install mhddfs -y
apt-get install samba -y
apt-get install upstart-sysv -y
update-initramfs -u
sudo apt-get purge systemd -y

pip3 install -r requirements.txt
python3 setup.py