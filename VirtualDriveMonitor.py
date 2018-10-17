import subprocess
import re
import datetime
import time
import os

class virtual_drive:
	#Local Variables
	know_drives = []
	detailed_drives = {}
	exclude_drives = []
	used_mounts = []
	virtual_drive_mount = "/mnt/virtual_drive"
	user = ""
	logfile = ""

	def __init__(self, exclude_file = ""):
		if exclude_file == "":
			return;

		#Open file with exclude lists
		read = open("exclude_drives.conf",'r')
		read = read.read()
		user = re.findall('(?<=Username=)(([a-z]|[A-Z]|[0-9]|\-|[_])+)', str(read));
		self.user = user[0][0]
		read = re.findall('(?<=Disk=)(([a-z]|[A-Z]|[0-9]|\-)+)',str(read))

		for i in read:
			self.exclude_drives.append(i[0])

		#Find drive mounted previuosly by the app
		mounts = str(subprocess.check_output(['df', '-h']))
		mounts = re.findall('(?<=[ ][\/]mnt[\/]drive)([0-9]+)', mounts)

		#Make list of used mounting points
		for i in range(60):
			self.used_mounts.append(False)

		#Update list
		temp = "\nDrive(s): "
		for i in mounts:
			self.used_mounts[int(i)] = True
			temp += i + ", "

		print(datetime.datetime.now())
		print(temp[:-2] + " already mounted.\n")

		#Make first drives scan
		self.add_drives()




	def add_drives(self):
		#Changes in attached devices
		changed = False

		#Disks to be added to the virtual disk
		jbod_folders = []
		#Query drive information
		did, dev, disks = self.get_information()
		current = self.know_drives
	
		#Found drives and previous drives
		found = set(did)
		current = set(current)

		#New attached drives and removed drives
		new_drives = found - current
		lost_drives = current - found
		
		print("\n*--------------------------------------------------------------------*\n")

		#If new frives found
		if len(new_drives) > 0:
			changed = True
			print(datetime.datetime.now())
			print("\nNew drives found: ")
			#Initial setup for registered drives
			for i in new_drives:
				found = False
				for a in range(len(did)):
					if i == did[a]:
						self.detailed_drives[i] = {}
						self.detailed_drives[i]['name'] = dev[a]
						self.detailed_drives[i]['active'] = True
						self.detailed_drives[i]['analized'] = False
						self.detailed_drives[i]['in_array'] = False
				for a in self.exclude_drives:
					if i == a:
						found = True
						break
				if found:
					print("\tDrive {0} ignored, found on exclude list".format(i))
					self.detailed_drives[i]['ignored'] = True
				else:
					print("\tDrive {0} detected, will be added to array".format(i))
					self.detailed_drives[i]['ignored'] = False
			print()

		#If drives where removed
		if len(lost_drives) > 0:
			changed = True
			print(datetime.datetime.now())
			print("\nDrives removed: ")
			for i in lost_drives:
				print("\tDrive {0} removed".format(i))
				#Mark them as inactive to later be unmounted
				self.detailed_drives[i]['active'] = False
			print()

		return_drives = self.detailed_drives
		if changed:
			count = 0
			folder = ""
			#print(mounts)
			for i in self.detailed_drives:
				#If drive haven't been analized
				if not(self.detailed_drives[i]['analized']):
					self.detailed_drives[i] = self.analize_drive(self.detailed_drives[i], disks)
				print(i + " :\n" + str(self.detailed_drives[i]))

				#Mount all drives that will be included in the virtual disk
				if not(self.detailed_drives[i]['ignored']) and self.detailed_drives[i]['active']:
					#If it has more than one partition is not configured
					if len(self.detailed_drives[i]['parts']) != 1:
						count = self.get_next_mount()
						self.detailed_drives[i], self.used_mounts = self.unmount(self.detailed_drives[i])
						return_drives, did, format = self.format_drive(i, self.detailed_drives, disks, count)

					else:
						#If the drive is mounted on another location that is not /mnt/drive<n> unmount it.
						if not(re.match("/mnt/drive[0-9]+", self.detailed_drives[i]['parts'][0]['mount'])):
							self.detailed_drives[i] = self.unmount(self.detailed_drives[i])
						
						#If drive is not mounted.
						count = self.get_next_mount()
						if not(self.detailed_drives[i]['mounted']):
							self.mount(self.detailed_drives[i], count)

						#Look for configuration file on drive
						res = str(subprocess.check_output(["ls",self.detailed_drives[i]['parts'][0]['mount']]))[:-3]
					
						#If file is present and has a single partition the drive is ready
						if i in res:
							print("\tDrive already set up\n")
							#Save drive information to add it into the array
							folder = self.detailed_drives[i]['parts'][0]['mount']
							self.detailed_drives[i]['in_array'] = True
						#If drive is no setup
						else:
							print("\tDrive not configured")
							#Format and setup the drive
							return_drives, did, folder = self.format_drive(i, disks)

						jbod_folders.append(folder)
			
				#If drive is excluded from the virtual disk
				elif self.detailed_drives[i]['ignored']:
					print("\tDrive ignored\n")

				#Unmount removed drives
				try:
					if self.detailed_drives[i]['mounted'] and not(self.detailed_drives[i]['active']):
						self.detailed_drives[i] = self.unmount(self.detailed_drives[i])
				except KeyError:
					pass

			#Unmount previous virtual drive
			subprocess.run(["umount", "-f", "-l", '/mnt/virtual_drive'])

			#If the path does not existe create it.
			if not(os.path.isdir("/mnt/virtual_drive")):
				os.mkdir("/mnt/virtual_drive")
			
			#If we have more than one drive create the virtual disk
			if len(jbod_folders) > 1:
				temp = ""
				for i in jbod_folders:
					temp += i + ","

				print("\nCreating Virtual Disk\n")
				
				#Using mhddfs We'll create a virtual disk with all of our drives
				for i in str(subprocess.check_output(['mhddfs', temp[:-1], '/mnt/virtual_drive', '-o', 'allow_other'])).split("\\n"):
					print(i.replace("b'",""))
		
			#If we only have one drive we'll use as a virtual drive for the share.
			else:
				print("Single Drive will be used.\n")
				for i in return_drives:
					#Look for the single active drive to mount it into the virtual drive.
					if return_drives[i]['active'] and not(return_drives[i]['ignored']) and return_drives[i]['mounted']:
						return_drives[i] = self.unmount(return_drives[i])
						return_drives[i]['parts'][0]['mount'] = "/mnt/virtual_drive"
						subprocess.run(["mount", return_drives[i]['parts'][0]['name'], return_drives[i]['parts'][0]['mount']])
						return_drives[i]['mounted'] = True
						print("\tDrive {0} mounted as Virtual Drive\n".format(return_drives[i]['name']))
						break

			#If the path does not existe create it.
			if not(os.path.isdir("/mnt/virtual_drive/storage")):
				os.mkdir("/mnt/virtual_drive/storage")
			subprocess.run(['chown', self.user, '/mnt/virtual_drive/storage']);

			#Report partition mount
			for i in str(subprocess.check_output(['df', '-h'])).split("\\n"):
				print(i.replace("b'",""))
		
		#If no changes on drives where detected
		else:
			print(datetime.datetime.now())
			print("\nNo Changes found\n")
		self.know_drives = did
		self.detailed_drives = return_drives


	#Get next available space
	def get_next_mount(self):
		for i in range(len(self.used_mounts)):
				if not(self.used_mounts[i]):
					return i


	#Format and setup current drive
	def format_drive(self, old_name, disks):
		print("\tDrive {0} is going to be formated".format(old_name))

		#Copy drive to be formated and current drives
		drive = self.detailed_drives[old_name]
		drives = self.detailed_drives
		
		#Unmount drive
		self.unmount(drive)
		#Create new partition table
		subprocess.run(['parted', '-s', drive['name'], 'mklabel', 'gpt', 'mkpart', 'primary', '0%', '100%'])
		time.sleep(5)
		#Write changes to dirsk
		subprocess.run(['mkfs.ext4', '-F',drive['name'] + "1"])

		#Setup drive
		drive['analized'] = False
		print("\tDrive Formated!")
		#mount drive
		drive = self.mount(drive, self.get_next_mount())
		#Get new drive id.
		name, did = self.find_drive(drive['name'])
		#Add drive to dictionary and remove old one
		drives[name] = drive
		del drives[old_name]

		#Create new config file
		f = open(drive['parts'][0]['mount'] + "/" + name,"w+")
		f.write('.')
		f.close
		print("\tDrive {0} configured\n".format(name))
		drive["in_array"] = True
		#Return results
		return drives, did, drive['parts'][0]['mount']


	#Mount drive on especific mount point
	def mount(self, drive, space):
		#Verify if folder exists and create it if needed
		if not(os.path.isdir("/mnt/drive" + str(space))):
			os.mkdir("/mnt/drive" + str(space))

		#Mount drive
		drive['parts'][0]['mount'] = "/mnt/drive" + str(space)
		subprocess.run(["mount", drive['parts'][0]['name'], drive['parts'][0]['mount']])
		drive['mounted'] = True
		print("\tDrive {0} mounted on {1}".format(drive['name'], drive['parts'][0]['mount']))
		#Register used mounts spaces
		self.used_mounts[space] = True

		return drive


	#Unmount drive
	def unmount(self, drive):
		#Iterate trough all drive partitions
		for i in range(len(drive['parts'])):
			part = drive['parts'][i]
			#If a partition is mounted unmount it
			if part['mount'] != "":
				subprocess.run(["umount", "-f", "-l", part["mount"]])
				print("\t{0} unmounted on {1}".format(part['name'], part['mount']))
				#Release de mount point if is a valid mount point for the virtual drive
				if re.match("/mnt/drive[0-9]+", part['mount']):
					self.used_mounts[int(re.search('[0-9]+', part['mount']).group(0))] = False
				part['mount'] = ""
				drive['parts'][i] = part
		drive['mounted'] = False
		print("\tDrive {0} fully unmounted\n".format(drive['name']))
		return drive

	#Find Drive ID
	def find_drive(self, drive):
		did, dev, i = self.get_information()
		#print(drive);
		for i in range(len(dev)):
			#print(dev[i]);
			if drive == dev[i]:
				return did[i], did
		return 0

	#Query drive informatino to OS
	def get_information(self):
		disks = subprocess.check_output(['fdisk', '-l'])
		disks = str(disks)

		#Parse /dev/ path and Drive ID.
		dev = re.findall('(?<=Disk )(/dev\/([0-9]|[a-z])+:)', disks)
		did = re.findall('(?<=Disk identifier: )(([a-z]|[A-Z]|[0-9]|\-)+)', disks)

		#Clean up information
		for i in range(len(did)):
			did[i] = did[i][0]
			dev[i] = dev[i][0][:-1]
		
		return did, dev, disks

	#Analize Hard Drive mounts
	def analize_drive(self, drive, disks):
		#Get list of mounted partitions
		mounts = str(subprocess.check_output(['df', '-h']))
		mounts = mounts.split('\\n')

		#Find all drive partitions
		parts = re.findall('({0}([a-z]|[0-9])+)'.format(drive['name']), disks)
		drive['parts'] = []
		#Is drive mounted?
		drive['mounted'] = False

		#Iterate trough all drive partitions to find any mounted partition
		for a in range(len(parts)):
			#Store the partition
			drive['parts'].append({'name': parts[a][0], 'mount':""})
			for x in mounts:
				#If the partition is mounted:
				if x.startswith(parts[a][0]):
					drive['mounted'] = True
					temp = x.split(' ')
					drive['parts'][a]['mount'] = temp[len(temp) - 1]
		#Mark drive as analized
		drive['analized'] = True
		return drive