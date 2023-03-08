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
                "Physical": drive.name,
                "Logical": logicalDisk.DeviceID
            }
            devices.append(diskPartition)
    return devices

# Read Physical Drive
def ReadPhysicalDrive(driveName, sectorBytes):
    with open(driveName, "rb") as drive:
        # Read Master Boot Record
        MBR = drive.read(sectorBytes)
        MBRInfo = []
        
        # Read 16-byte partition in MBR
        for i in range(int("1BE", 16), sectorBytes, 16):
            if i + 16 > sectorBytes:
                break
            MBRPart = {
                "Status": MBR[i],
                "CHSBegin": int.from_bytes(MBR[i + int("01", 16) : i + int("01", 16) + 3], "little"),
                "Type": MBR[i + int("04", 16)],
                "CHSEnd": int.from_bytes(MBR[i + int("05", 16) : i + int("05", 16) + 3], "little"),
                "LBABegin": int.from_bytes(MBR[i + int("08", 16) : i + int("08", 16) + 4], "little"),
                "Sectors": int.from_bytes(MBR[i + int("0C", 16) : i + int("0C", 16) + 4], "little")
            }
            if MBRPart["CHSBegin"] > 0:
                MBRInfo.append(MBRPart)
            else:
                break 

        # Read partitions
        for MBRPart in MBRInfo:
            # 7 = 0x07 (NTFS)
            if MBRPart["Type"] == 7:
                ReadNTFSPartition(driveName, sectorBytes, MBRPart["LBABegin"])
            # 12 = 0x0C (FAT32)
            elif MBRPart["Type"] == 12:
                bootSectorInfo = ReadFAT32BootSector(driveName, sectorBytes, MBRPart["LBABegin"])
                ReadFAT32RDET(driveName, sectorBytes, MBRPart["LBABegin"] + bootSectorInfo["SectorsBeforeFAT"] + bootSectorInfo["FATTables"] * bootSectorInfo["FATSectors"])
            else:
                print("Unknown parition type") 

# Read NTFS partition
def ReadNTFSPartition(driveName, sectorBytes, LBAbegin):
    print("Can't read NTFS now!")

# Read FAT32 partition
def ReadFAT32BootSector(driveName, sectorBytes, LBAbegin):
    bootSectorInfo = {}

    with open(driveName, "rb") as drive:
        drive.seek(LBAbegin * 32 * 16)
        bootSector = drive.read(sectorBytes)

        bootSectorInfo = {
            "SectorBytes": int.from_bytes(bootSector[int("0B", 16) : int("0B", 16) + 2], "little"),
            "ClusterSectors": bootSector[int("0D", 16)],
            "SectorsBeforeFAT": int.from_bytes(bootSector[int("0E", 16) : int("0E", 16) + 2], "little"),
            "FATTables": bootSector[int("10", 16)],
            "VolumeSectors": int.from_bytes(bootSector[int("20", 16) : int("20", 16) + 4], "little"),
            "FATSectors": int.from_bytes(bootSector[int("24", 16) : int("24", 16) + 4], "little"),
            "RDETClusterBegin": int.from_bytes(bootSector[int("2C", 16) : int("2C", 16) + 4], "little"),
            "FATType": bootSector[int("52", 16) : int("52", 16) + 8],
        }

    return bootSectorInfo

# Read FAT32 RDET
def ReadFAT32RDET(driveName, sectorBytes, sectorBegin):
    with open(driveName, "rb") as drive:
        drive.seek(sectorBegin * 32 * 16)
        RDET = drive.read(sectorBytes)

        # Entry size is 32B
        for i in range(0, sectorBytes, 32):
            # Sub entry
            # Entry
            entry = {
                "Name": RDET[i : i + 8],
                "ExtendedName": RDET[i + int("08", 16) : i + int("08", 16) + 3],
                "Attributes": "{0:08b}".format(RDET[i + int("0B", 16)]),
                "TimeCreated": int.from_bytes(RDET[i + int("0D", 16) : i + int("0D", 16) + 3], "little"),
                "DateCreated": int.from_bytes(RDET[i + int("10", 16) : i + int("10", 16) + 2], "little"),
                "ClusterBegin": int.from_bytes(RDET[i + int("1A", 16) : i + int("1A", 16) + 2], "little"),
                "Size": int.from_bytes(RDET[i + int("1C", 16) : i + int("1C", 16) + 4], "little"),
            }
            print(entry)


# Test functions
USBDrives = GetUSBDrive()
USBPartitions = []
for drive in USBDrives:
    USBPartitions += GetUSBPartitions(drive)

ReadPhysicalDrive(USBDrives[0].name, USBDrives[0].BytesperSector)