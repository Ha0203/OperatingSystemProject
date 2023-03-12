import wmi
from queue import LifoQueue

# Get USB physical drives
def GetUSBDrive():
    c = wmi.WMI()
    devices = []
    for drive in c.Win32_DiskDrive():
        if "USB" in drive.Caption:
            devices.append(drive)
    return devices

# Read Physical Drive
def ReadPhysicalDrive(driveName, sectorBytes):
    partitions = []

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
                NTFSHierarchy = ReadNTFSPartition(driveName, sectorBytes, MBRPart["LBABegin"])
                partition = {
                    "Format": "NTFS",
                    "Hierarchy": NTFSHierarchy
                }
                partitions.append(partition)
            # 12 = 0x0C (FAT32)
            elif MBRPart["Type"] == 12:
                FAT32Hierarchy = ReadFAT32Partition(driveName, sectorBytes, MBRPart["LBABegin"])
                partition = {
                    "Format": "FAT32",
                    "Hierarchy": FAT32Hierarchy
                }
                partitions.append(partition)
            else:
                print("Unknown parition type") 
    
    return partitions

# Read NTFS partition
def ReadNTFSPartition(driveName, sectorBytes, LBAbegin):
    diskHierarchy = []
    with open(driveName, "rb") as drive:
        drive.seek(LBAbegin * 512)
        volumeBootRecord = drive.read(sectorBytes)
        volumeBootRecordInfo={
            "BytePerSector": int.from_bytes(volumeBootRecord[int("0B", 16) : int("0B", 16) + 2], "little"),
            "SectorPerCluster": volumeBootRecord[int("0D", 16)],
            "SectorPerTrack": int.from_bytes(volumeBootRecord[int("18", 16) : int("18", 16) + 2], "little"),
            "Head": int.from_bytes(volumeBootRecord[int("1A", 16) : int("1A", 16) + 2], "little"),
            "TotalSectors": int.from_bytes(volumeBootRecord[int("28", 16) : int("28", 16) + 8], "little"),
            "MFTStartCluster": int.from_bytes(volumeBootRecord[int("30", 16) : int("30", 16) + 8], "little"),
            "MFTStartClusterSecondary": int.from_bytes(volumeBootRecord[int("38", 16) : int("38", 16) + 8], "little"),
            "BytePerEntryMFT": volumeBootRecord[int("40", 16)],
        }

    return diskHierarchy

# Read FAT32 partition
def ReadFAT32Partition(driveName, sectorBytes, LBAbegin):
    diskHierarchy = []
    diskHierarchyCount = -1

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

        RDETSectorBegin = LBAbegin + bootSectorInfo["SectorsBeforeFAT"] + bootSectorInfo["FATTables"] * bootSectorInfo["FATSectors"]
        drive.seek(RDETSectorBegin * 32 * 16)
        while(True):            
            RDET = drive.read(sectorBytes)
            entryQueue = LifoQueue()

            # Entry size is 32B
            for i in range(0, sectorBytes, 32):
                # Break the read while loop
                if RDET[i] == 0:
                    break
                # Skip if deleted
                if RDET[i] == 229: # 229 = 0xE5
                    continue            
                if RDET[i + int("0B", 16)] == 15: # 15 = 0x0F
                # Sub entry
                    subEntry = {
                        "Name1": RDET[i + int("01", 16) : i + int("01", 16) + 10].decode("utf-16"),
                        "Name2": RDET[i + int("0E", 16) : i + int("0E", 16) + 12].decode("utf-16"),
                        "Name3": RDET[i + int("1C", 16) : i + int("1C", 16) + 4].decode("utf-16")
                    }
                    entryQueue.put(subEntry)
                else:
                # Entry
                    # Get entry full name
                    entryName = ""
                    while not entryQueue.empty():
                        subEntry = entryQueue.get()
                        for j in range(1, 4):
                            entryName += subEntry["Name" + str(j)]
                    entryName = entryName[:entryName.find("\x00")]

                    entry = {
                        "Name": entryName,
                        "PrimaryName": RDET[i : i + 8].decode("utf-8"),
                        "ExtendedName": RDET[i + int("08", 16) : i + int("08", 16) + 3].decode("utf-8"),
                        "Attributes": GetFAT32FileAttributes("{0:08b}".format(RDET[i + int("0B", 16)])),
                        "TimeCreated": GetFAT32FileTimeCreated("".join(format(byte, '08b') for byte in RDET[i + int("0D", 16) : i + int("0D", 16) + 3][::-1])),
                        "DateCreated": GetFAT32FileDateCreated("".join(format(byte, '08b') for byte in RDET[i + int("10", 16) : i + int("10", 16) + 2][::-1])),
                        "ClusterBegin": int.from_bytes(RDET[i + int("1A", 16) : i + int("1A", 16) + 2], "little"),
                        "Size": int.from_bytes(RDET[i + int("1C", 16) : i + int("1C", 16) + 4], "little")
                    }
                    item = {
                        "Parent": -1,
                        "Type": "Folder" if "Directory" in entry["Attributes"] else "File",
                        "Name": entry["Name"] if entry["Name"] != "" else entry["PrimaryName"] + entry["ExtendedName"],
                        "Attributes": entry["Attributes"],
                        "TimeCreated": entry["TimeCreated"],
                        "DateCreated": entry["DateCreated"],
                        "Size": entry["Size"],
                    }
                    diskHierarchy.append(item)
                    diskHierarchyCount += 1
                    if "Directory" in entry["Attributes"] and not "Archive" in entry["Attributes"]:                
                        diskHierarchyCount = ReadFAT32Data(driveName, sectorBytes, bootSectorInfo, RDETSectorBegin, entry["ClusterBegin"], diskHierarchy, diskHierarchyCount, diskHierarchyCount)            
            else:
                continue
            break

    return diskHierarchy

# Read FAT32 Data
def ReadFAT32Data(driveName, sectorBytes, bootSectorInfo, RDETSectorBegin, clusterBegin, diskHierarchy, parent, diskHierarchyCount):
    sectorBegin = RDETSectorBegin + (clusterBegin - bootSectorInfo["RDETClusterBegin"]) * bootSectorInfo["ClusterSectors"]
    
    with open(driveName, "rb") as drive:
        drive.seek(sectorBegin * 32 * 16)

        data = drive.read(sectorBytes) 
        entryQueue = LifoQueue()     

        for i in range(0, sectorBytes, 32):
            if data[i] == 0:
                break
            # Skip if deleted
            if data[i] == 229 or data[i] == 46: # 229 = 0xE5
                continue  
            if data[i + int("0B", 16)] == 15: # 15 = 0x0F
            # Sub entry
                subEntry = {
                    "Name1": data[i + int("01", 16) : i + int("01", 16) + 10].decode("utf-16"),
                    "Name2": data[i + int("0E", 16) : i + int("0E", 16) + 12].decode("utf-16"),
                    "Name3": data[i + int("1C", 16) : i + int("1C", 16) + 4].decode("utf-16")
                }
                entryQueue.put(subEntry)
            else:
            # Entry
                # Get entry full name
                entryName = ""
                while not entryQueue.empty():
                    subEntry = entryQueue.get()
                    for j in range(1, 4):
                        entryName += subEntry["Name" + str(j)]
                entryName = entryName[:entryName.find("\x00")]

                entry = {
                    "Name": entryName,
                    "PrimaryName": data[i : i + 8].decode("utf-8"),
                    "ExtendedName": data[i + int("08", 16) : i + int("08", 16) + 3].decode("utf-8"),
                    "Attributes": GetFAT32FileAttributes("{0:08b}".format(data[i + int("0B", 16)])),
                    "TimeCreated": GetFAT32FileTimeCreated("".join(format(byte, '08b') for byte in data[i + int("0D", 16) : i + int("0D", 16) + 3][::-1])),
                    "DateCreated": GetFAT32FileDateCreated("".join(format(byte, '08b') for byte in data[i + int("10", 16) : i + int("10", 16) + 2][::-1])),
                    "ClusterBegin": int.from_bytes(data[i + int("1A", 16) : i + int("1A", 16) + 2], "little"),
                    "Size": int.from_bytes(data[i + int("1C", 16) : i + int("1C", 16) + 4], "little")
                }
                item = {
                    "Parent": parent,
                    "Type": "Folder" if "Directory" in entry["Attributes"] else "File",
                    "Name": entry["Name"] if entry["Name"] != "" else entry["PrimaryName"] + entry["ExtendedName"],
                    "Attributes": entry["Attributes"],
                    "TimeCreated": entry["TimeCreated"],
                    "DateCreated": entry["DateCreated"],
                    "Size": entry["Size"],
                }
                diskHierarchy.append(item)
                diskHierarchyCount += 1
                if "Directory" in entry["Attributes"] and not "Archive" in entry["Attributes"]:
                    diskHierarchyCount = ReadFAT32Data(driveName, sectorBytes, bootSectorInfo, RDETSectorBegin, entry["ClusterBegin"], diskHierarchy, diskHierarchyCount, diskHierarchyCount)

    return diskHierarchyCount

# Get FAT32 file attributes
def GetFAT32FileAttributes(bitArray):
    attributes = []
    if bitArray[7] == "1":
        attributes.append("ReadOnly")
    if bitArray[6] == "1":
        attributes.append("Hidden")
    if bitArray[5] == "1":
        attributes.append("System")
    if bitArray[4] == "1":
        attributes.append("VolLabel")
    if bitArray[3] == "1":
        attributes.append("Directory")
    if bitArray[2] == "1":
        attributes.append("Archive")
    return attributes

# Get FAT32 file time created
def GetFAT32FileTimeCreated(bitArray):
    return {
        "Hour": int("".join(str(x) for x in bitArray[:5]), 2),
        "Minute": int("".join(str(x) for x in bitArray[5:11]), 2),
        "Second": int("".join(str(x) for x in bitArray[11:17]), 2),
        "MiliSecond": int("".join(str(x) for x in bitArray[17:]), 2),
    }

# Get FAT32 file date created
def GetFAT32FileDateCreated(bitArray):
    return {
        "Year": int("".join(str(x) for x in bitArray[:7]), 2) + 1980,
        "Month": int("".join(str(x) for x in bitArray[7:11]), 2),
        "Day": int("".join(str(x) for x in bitArray[11:]), 2)
    }

# Print FAT32 item
def PrintFAT32Item(item):
    print("{")
    print("    Name:", item["Name"])
    print("    Attributes:", item["Attributes"])
    print("    Date Created:", item["DateCreated"])
    print("    Time Created:", item["TimeCreated"])
    print("    Size:", item["Size"])
    print("}")

# Show sector content as hex
def PrintSectorBytes(sector):    
    i = -1
    for byte in sector:
        print("{:02x} ".format(byte), end="")
        i+=1
        if (i % 16 == 15):
            print("\n")

# Main
USBDrives = GetUSBDrive()
diskPartitions = ReadPhysicalDrive(USBDrives[0].name, USBDrives[0].BytesperSector)