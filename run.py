import pyudev
import datetime
from VirtualDriveMonitor import virtual_drive

#Device monitor setup
context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('block')

scanner = virtual_drive("exclude_drives.conf")

#Undefined loop to monitor for new drives
while True:
	for device in iter(monitor.poll, None):
			#If a devices changes on a SATA port:
			if 'ata' in str(device):
				print("\n*--------------------------------------------------------------------*\n")
				print('Triggered by: {0} - {1} [{2}]'.format(device.action, device.device_node, device))
				scanner.add_drives()
				break;
