import wmi

# Get USB physical drives
def GetUSBDrive():
    c = wmi.WMI()
    devices = []
    for drive in c.Win32_DiskDrive():
        if "USB" in drive.Caption:
            devices.append(drive)
    return devices

# Get USB drive partitions
def GetUSBPartitions(drive):
    devices = []
    partitions = drive.associators("Win32_DiskDriveToDiskPartition")
    for partition in partitions:
        logicalDisks = partition.associators("Win32_LogicalDiskToPartition")
        for logicalDisk in logicalDisks:
            diskPartition = {
                "physical": drive.name,
                "logical": logicalDisk.DeviceID
            }
            devices.append(diskPartition)
    return devices

# Read Physical Drive
def ReadPhysicalDrive(driveName):
    with open(driveName, "rb") as drive:
        # Read Master Boot Record
        MBR = drive.read(512)
        MBRInfo = []
        
        # Read 16-byte partition in MBR
        for i in range(int("1BE", 16), 512, 16):
            if i + 16 > 512:
                break
            MBRPart = {
                "CHSbegin": int.from_bytes(MBR[i + int("01", 16) : i + int("01", 16) + 3], "little"),
                "type": MBR[i + int("04", 16)],
                "CHSend": int.from_bytes(MBR[i + int("05", 16) : i + int("05", 16) + 3], "little"),
                "LBAbegin": int.from_bytes(MBR[i + int("08", 16) : i + int("08", 16) + 4], "little"),
                "sectors": int.from_bytes(MBR[i + int("0C", 16) : i + int("0C", 16) + 4], "little")
            }
            MBRInfo.append(MBRPart)
            print(MBRPart)  # test        


# Test functions
USBDrives = GetUSBDrive()
USBPartitions = []
for drive in USBDrives:
    USBPartitions += GetUSBPartitions(drive)
print(USBPartitions)

ReadPhysicalDrive(USBDrives[0].name)