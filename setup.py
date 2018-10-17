import subprocess
from VirtualDriveMonitor import virtual_drive
import re;
import os

dev = virtual_drive();

print("""PyDriveMonitor, Writen by David Astorga on October 2018
This software is designed to handle a JBOD disk array that will add/remove disk automaticaly.

This setup will allow you to set the exeption disk that will not be formated and included in the array.

please be aware that any SATA disk not included in the exeption list that is pluged into the computer while the program is running WILL BE FORMATED
""")

drives = {}
res = str(subprocess.check_output(['hwinfo', '--disk', '--short'])).split("\\n")
#print(res)
print("Disks available:")
for i in range(1, len(res) - 1):
	print("\t{1} -{0}".format(res[i], i));
print()
did, dev, t = dev.get_information();

for i in range(len(dev)):
	drives[dev[i]]=did[i];

print("Type 0 to add all drives to exeption list or type the numbers one by one and type \"D\" when done.")

file = open("exclude_drives.conf","w+")
while True:
	selection = input("input D, drive number or 0 to add all:");
	if selection == '0':
		for i in did:
			file.write("Disk=" + i + "\n");
		break;
	elif selection == "D" or selection == "d":
		break;

	elif selection.isnumeric():
		disk = re.findall("(/dev/(([0-9]|[a-z]|[A-Z])+))", res[int(selection)])[0][0]
		file.write("Disk=" + drives[disk] + "\n");

	else:
		print("Invalid option, try again.")


user = input("\nPlease type the user that you'll use to connect to the shared drive: ");
file.write("Username=" + user)
file.close();

print()
subprocess.run(["useradd", user, "--shell", "/bin/false"])

subprocess.run(["sudo", "smbpasswd", "-a", user])

if os.path.isfile("/etc/samba/smb.conf.bak"):
	subprocess.run(["cp", "/etc/samba/smb.conf.bak", "/etc/samba/smb.conf"])
else:
	subprocess.run(["cp", "/etc/samba/smb.conf", "/etc/samba/smb.conf.bak"])

file = open("/etc/samba/smb.conf", "a+")

file.write("""

[NVR_Storage]
path = /mnt/virtual_drive/storage
valid users = {0}
read only = no\n""".format(user))

subprocess.run(["sudo", "service", "smbd", "restart"])
file.close();

print();
while True:
	selection = input("Run at start up? (y/n): ");
	if selection == 'y' or selection == "Y":
		conf = open("/etc/init/VirtualDriveMonitor.conf", "w+")
		conf.write("""#This scrpt is generated by VirtualDriveMonitor and is inteded to initiate the service that will keep your
#Virtual disk up to date
#Writen by David Astorga

start on runlevel [2345]
console log

script
cd {0}
python3 run.py
end script""".format(os.getcwd()));
		break;
	elif selection == 'n' or selection == 'N':
		break;

print("Setup completed, please run \"python3 run.py\" as sudo to start the virtual drive or reboot your system is you selected to run at startup.")