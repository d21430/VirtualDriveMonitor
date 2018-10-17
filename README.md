# VirtualDriveMonitor
Virtual drive creation with mhddfs

This piece of code allows to create virtual drives merging multiple physical drives without using a RAID Array and by hence no redundancy and no need to rebuild the whole array every time that you add/remove a drive.

This code also allows you to use the full capacity if your drives without having all your information lost when a drive dies, you'll only loose what's stored on that specific drive.

This utility is based on mhddfs to create a virtual drive and Samba to share that virtual drive with another computers.

In order to use this software, you only need to clone the repository and run the install.sh script, this will install all dependencies and run the setup program where you'll be asked to select the drives that want to NOT be included in the array. Also, you'll be asked for the samba username and password for the share.

Please bear in mind that this code is intended for a security camera footage storage, so any new drive added to the computer will be FORMATED and added to de array.

This is just the first release, more detailed description and instructions are to come, as well more options and settings.

Thanks for your help
