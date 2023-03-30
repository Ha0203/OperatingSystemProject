import wmi
from queue import LifoQueue
from datetime import datetime
import datetime


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
                NTFSHierarchy = ReadNTFSPartition(driveName, sectorBytes, MBRPart["LBABegin"], drive)
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
def ReadNTFSPartition(driveName, sectorBytes, LBAbegin, drive):
    diskHierarchy = []
    drive.seek(LBAbegin * 512)
    
    volumeBootRecord = drive.read(sectorBytes)
    #Read NTFS Volume boot record
    volumeBootRecordInfo={
        "BytePerSector": int.from_bytes(volumeBootRecord[int("0B", 16) : int("0B", 16) + 2], "little"),
        "SectorPerCluster": volumeBootRecord[int("0D", 16)],
        "SectorPerTrack": int.from_bytes(volumeBootRecord[int("18", 16) : int("18", 16) + 2], "little"),
        "Head": int.from_bytes(volumeBootRecord[int("1A", 16) : int("1A", 16) + 2], "little"),
        "TotalSectors": int.from_bytes(volumeBootRecord[int("28", 16) : int("28", 16) + 8], "little"),
        "MFTStartCluster": int.from_bytes(volumeBootRecord[int("30", 16) : int("30", 16) + 8], "little"),
        "MFTStartClusterSecondary": int.from_bytes(volumeBootRecord[int("38", 16) : int("38", 16) + 8], "little"),
        "BytePerEntryMFT": pow(2,abs(twos_complement_to_integer("".join(format(byte, '08b') for byte in volumeBootRecord[int("40", 16) : int("40", 16) + 1][::-1]))))
    }
    
    MFTSectorBegin = LBAbegin + volumeBootRecordInfo["MFTStartCluster"] * volumeBootRecordInfo["SectorPerCluster"]
    
    #Read NTFS MFT
    
    n = MFTSectorBegin * sectorBytes #Variable to run through every MFT entries
    
    while True: #Loop read each entry
        drive.seek(n)
        MFTEntry = drive.read(volumeBootRecordInfo["BytePerEntryMFT"])
        
        MFTEntryHeaderInfo={
            "Signal": MFTEntry[int("00", 16) : int("00", 16) + 4].decode("utf-8"),
            "FirstAtt": int.from_bytes(MFTEntry[int("14", 16) : int("14", 16) + 2], "little"),
            "State": int.from_bytes(MFTEntry[int("16", 16) : int("16", 16) + 2], "little"),
            "BytesUsed": int.from_bytes(MFTEntry[int("18", 16) : int("18", 16) + 4], "little"),
            "Bytes": int.from_bytes(MFTEntry[int("1C", 16) : int("1C", 16) + 4], "little"),
            "ID": int.from_bytes(MFTEntry[int("2C", 16) : int("2C", 16) + 4], "little")
        }
        if MFTEntryHeaderInfo["Signal"] != "FILE" and MFTEntryHeaderInfo["Signal"] != "BAAD":
            break
        if MFTEntryHeaderInfo["State"] == 0 or MFTEntryHeaderInfo["State"] == 2: #Ignore deleted folder/file
            n += volumeBootRecordInfo["BytePerEntryMFT"] #Move to the next entry
            continue
        
        i = MFTEntryHeaderInfo["FirstAtt"] #Variable to run through every attributes in MFT entry
        
        #while loop
        item={
                "Parent": -1,
                "ID": MFTEntryHeaderInfo["ID"],
                "Type": "",
                "Name": "",
                "Attributes": [],
                "TimeCreated": "",
                "DateCreated": "",
                "Size": ""
            }
        filesize = 0
        entryDataRunned = 0
        while True:
            checktype = int.from_bytes(MFTEntry[int("00", 16) + i : int("00",16) + 4 + i], "little")
            if(checktype != 4294967295): #Attribute End 0xFFFF
                AttributeHeaderInfo={
                    "Type": int.from_bytes(MFTEntry[int("00", 16) + i : int("00",16) + 4 + i], "little"),
                    "Size": int.from_bytes(MFTEntry[int("04", 16) + i : int("04",16) + 2 + i], "little"),
                    "IsNonRes": MFTEntry[int("08", 16) + i],
                    "SizeContent": int.from_bytes(MFTEntry[int("10", 16) + i : int("10",16) + 4 + i], "little"),
                    "PosContent": int.from_bytes(MFTEntry[int("14", 16) + i : int("14",16) + 2 + i], "little")
                }
            else:
                AttributeHeaderInfo={
                    "Type": int.from_bytes(MFTEntry[int("00", 16) + i : int("00",16) + 4 + i], "little")
                }
            if AttributeHeaderInfo["Type"] == 16 or AttributeHeaderInfo["Type"] == 48:
                k = AttributeHeaderInfo["PosContent"] + i
            
            if AttributeHeaderInfo["Type"] == 16: #Attribute Standard Information 0x0010
                item["TimeCreated"] = GetNTFSFileTimeCreated(int.from_bytes(MFTEntry[int("00", 16) + k : int("00",16) + 8 + k], "little"))
                item["DateCreated"] = GetNTFSFileDateCreated(int.from_bytes(MFTEntry[int("00", 16) + k : int("00",16) + 8 +k], "little"))
                
            if AttributeHeaderInfo["Type"] == 48: #Attribute File Name 0x0030
                item["Parent"] = int.from_bytes(MFTEntry[int("00", 16) + k: int("00",16) + 6 +k], "little")
                lengthName = MFTEntry[int("40", 16) + k]
                item["Name"] = MFTEntry[int("42", 16) + k: int("42",16) + lengthName * 2 + k].decode("utf-16")
                item["Attributes"] = GetNTFSFileAttributes(''.join(format(byte, '08b') for byte in MFTEntry[int("38", 16) + k: int("38",16) + 4 + k][::-1]))
            
            elif AttributeHeaderInfo["Type"] == 128: #Attribute Data 0x0080
                if AttributeHeaderInfo["IsNonRes"] == 0 and entryDataRunned == 0:
                    filesize += int.from_bytes(MFTEntry[int("10", 16) + i : int("10",16) + 4 + i], "little")
                    entryDataRunned = 1
                if AttributeHeaderInfo["IsNonRes"] == 1 and entryDataRunned == 0:
                    filesize += int.from_bytes(MFTEntry[int("30", 16) + i : int("30",16) + 8 + i], "little")
                    entryDataRunned = 1
            elif AttributeHeaderInfo["Type"] == 4294967295: #Attribute End 0xFFFF
                break
            i += AttributeHeaderInfo["Size"]
        
        if "Directory" in item["Attributes"]:
            item["Type"] = "Folder"
        else:
            item["Type"] = "File"
        item["Size"] = filesize
        
        diskHierarchy.append(item)
    
        if MFTEntryHeaderInfo["ID"] == 11:
            n += 13 * volumeBootRecordInfo["BytePerEntryMFT"] #Skip to $Quota entry
        elif MFTEntryHeaderInfo["ID"] == 26:
            n += 13 * volumeBootRecordInfo["BytePerEntryMFT"] #Skip to user's entry
        else: 
            n += volumeBootRecordInfo["BytePerEntryMFT"]
        
    for item in diskHierarchy:
        if item["Parent"] != -1 and item["Type"] == "File" and item["Parent"] != 5:
            updateSize(diskHierarchy,item["Size"], item["Parent"])         
    
    return diskHierarchy

def updateSize(diskHierarchy, size, id):
    for item in diskHierarchy:
        if item["ID"] == id:
            item["Size"] += size
            if item["ID"] == item["Parent"]:
                return
            if item["Parent"] != -1:
                updateSize(diskHierarchy, size, item["Parent"])
            return
    
    
    

# Read FAT32 partition
def ReadFAT32Partition(driveName, sectorBytes, LBAbegin):
    diskHierarchy = []
    diskHierarchyCount = -1

    with open(driveName, "rb") as drive:
        drive.seek(LBAbegin * sectorBytes)
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

        clustersChain = ReadFAT32Table(driveName, sectorBytes, LBAbegin + bootSectorInfo["SectorsBeforeFAT"], bootSectorInfo["FATSectors"])

        dataSectorBegin = LBAbegin + bootSectorInfo["SectorsBeforeFAT"] + bootSectorInfo["FATTables"] * bootSectorInfo["FATSectors"]
        entryQueue = LifoQueue()
        cluster = bootSectorInfo["RDETClusterBegin"]

        while True:  
            drive.seek((dataSectorBegin + (cluster - 2) * bootSectorInfo["ClusterSectors"]) * sectorBytes)
            for sec in range(0, bootSectorInfo["ClusterSectors"]):       
                RDET = drive.read(sectorBytes)            

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
                        removePos = entryName.find("\x00")
                        if removePos > 0:
                            entryName = entryName[:entryName.find("\x00")]

                        entry = {
                            "Name": entryName,
                            "PrimaryName": RDET[i : i + 8].decode("latin-1"),
                            "ExtendedName": RDET[i + int("08", 16) : i + int("08", 16) + 3].decode("latin-1"),
                            "Attributes": GetFAT32FileAttributes("{0:08b}".format(RDET[i + int("0B", 16)])),
                            "TimeCreated": GetFAT32FileTimeCreated("".join(format(byte, '08b') for byte in RDET[i + int("0D", 16) : i + int("0D", 16) + 3][::-1])),
                            "DateCreated": GetFAT32FileDateCreated("".join(format(byte, '08b') for byte in RDET[i + int("10", 16) : i + int("10", 16) + 2][::-1])),
                            "HighCluster": int.from_bytes(RDET[i + int("14", 16) : i + int("14", 16) + 2], "little"),
                            "ClusterBegin": int.from_bytes(RDET[i + int("1A", 16) : i + int("1A", 16) + 2], "little"),
                            "Size": int.from_bytes(RDET[i + int("1C", 16) : i + int("1C", 16) + 4], "little")
                        }

                        if entry["Name"] == "":
                            if entry["ExtendedName"].rstrip() != "":
                                entry["Name"] = (entry["PrimaryName"].rstrip() + "." + entry["ExtendedName"]).lower()
                            else:
                                entry["Name"] = (entry["PrimaryName"].rstrip() + entry["ExtendedName"]).lower()
                        item = {
                            "Parent": -1,
                            "Type": "Folder" if "Directory" in entry["Attributes"] else "File",
                            "Name": entry["Name"],
                            "Attributes": entry["Attributes"],
                            "TimeCreated": entry["TimeCreated"],
                            "DateCreated": entry["DateCreated"],
                            "Size": entry["Size"],
                        }
                        diskHierarchy.append(item)
                        diskHierarchyCount += 1
                        if "Directory" in entry["Attributes"] and not "Archive" in entry["Attributes"]:   
                            diskHierarchyCount = ReadFAT32Data(driveName, sectorBytes, bootSectorInfo, dataSectorBegin, clustersChain, (entry["HighCluster"] << 16) + entry["ClusterBegin"], diskHierarchy, diskHierarchyCount, diskHierarchyCount)            
                else:
                    continue
                break
            cluster = clustersChain[cluster]
            if cluster == int(0xFFFFFFFF) or cluster == int(0x0FFFFFF8) or cluster == int(0x0FFFFFFF):
                break
    
    for item in reversed(diskHierarchy):
        if item["Parent"] >= 0:
            diskHierarchy[item["Parent"]]["Size"] += item["Size"]

    return diskHierarchy

# Read FAT32 FAT Table
def ReadFAT32Table(driveName, sectorBytes, FATBegin, FATSectors):
    clustersChain = []
    with open(driveName, "rb") as drive:
        drive.seek(FATBegin * sectorBytes)
        
        for i in range(0, FATSectors):
            FAT = drive.read(sectorBytes)
            for j in range(0, sectorBytes, 4):
                nextCluster = int.from_bytes(FAT[j : j + 4], "little")
                clustersChain.append(nextCluster)
    
    return clustersChain

# Read FAT32 Data
def ReadFAT32Data(driveName, sectorBytes, bootSectorInfo, dataSectorBegin, clustersChain, clusterBegin, diskHierarchy, parent, diskHierarchyCount):   
    with open(driveName, "rb") as drive:
        cluster = clusterBegin     
        entryQueue = LifoQueue()       

        # Read in a cluster
        while True:
            drive.seek((dataSectorBegin + (cluster - 2) * bootSectorInfo["ClusterSectors"]) * sectorBytes)
            for sec in range(0, bootSectorInfo["ClusterSectors"]):   
                data = drive.read(sectorBytes)             

                for i in range(0, sectorBytes, 32):
                    # Break the read for loop
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
                        removePos = entryName.find("\x00")
                        if removePos > 0:
                            entryName = entryName[:entryName.find("\x00")]

                        entry = {
                            "Name": entryName,
                            "PrimaryName": data[i : i + 8].decode("latin-1"),
                            "ExtendedName": data[i + int("08", 16) : i + int("08", 16) + 3].decode("latin-1"),
                            "Attributes": GetFAT32FileAttributes("{0:08b}".format(data[i + int("0B", 16)])),
                            "TimeCreated": GetFAT32FileTimeCreated("".join(format(byte, '08b') for byte in data[i + int("0D", 16) : i + int("0D", 16) + 3][::-1])),
                            "DateCreated": GetFAT32FileDateCreated("".join(format(byte, '08b') for byte in data[i + int("10", 16) : i + int("10", 16) + 2][::-1])),
                            "HighCluster": int.from_bytes(data[i + int("14", 16) : i + int("14", 16) + 2], "little"),
                            "ClusterBegin": int.from_bytes(data[i + int("1A", 16) : i + int("1A", 16) + 2], "little"),
                            "Size": int.from_bytes(data[i + int("1C", 16) : i + int("1C", 16) + 4], "little")
                        }
                        if entry["Name"] == "":
                            if entry["ExtendedName"].rstrip() != "":
                                entry["Name"] = (entry["PrimaryName"].rstrip() + "." + entry["ExtendedName"]).lower()
                            else:
                                entry["Name"] = (entry["PrimaryName"].rstrip() + entry["ExtendedName"]).lower()
                        item = {
                            "Parent": parent,
                            "Type": "Folder" if "Directory" in entry["Attributes"] else "File",
                            "Name": entry["Name"],
                            "Attributes": entry["Attributes"],
                            "TimeCreated": entry["TimeCreated"],
                            "DateCreated": entry["DateCreated"],
                            "Size": entry["Size"],
                        }
                        diskHierarchy.append(item)
                        diskHierarchyCount += 1
                        if "Directory" in entry["Attributes"] and not "Archive" in entry["Attributes"]:
                            diskHierarchyCount = ReadFAT32Data(driveName, sectorBytes, bootSectorInfo, dataSectorBegin, clustersChain, (entry["HighCluster"] << 16) + entry["ClusterBegin"], diskHierarchy, diskHierarchyCount, diskHierarchyCount)
                else:
                    continue
                break
            cluster = clustersChain[cluster]
            if cluster == int(0xFFFFFFFF) or cluster == int(0x0FFFFFF8) or cluster == int(0x0FFFFFFF):
                break

    return diskHierarchyCount

# Get NTFS file Date created
def GetNTFSFileDateCreated(ticks):
    date_start = '1601-01-01 00:00:00'
    date_fromstr = datetime.datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
    converted_ticks = date_fromstr + datetime.timedelta(hours = 7) + datetime.timedelta(microseconds = ticks/10)
    return{
        "Year": converted_ticks.strftime("%Y"),
        "Month": converted_ticks.strftime("%m"),
        "Day": converted_ticks.strftime("%d")
    }

# Get NTFS file time created
def GetNTFSFileTimeCreated(ticks):
    date_start = '1601-01-01 00:00:00'
    date_fromstr = datetime.datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
    converted_ticks = date_fromstr + datetime.timedelta(hours = 7) + datetime.timedelta(microseconds = ticks/10)
    return{
        "Hour": converted_ticks.strftime("%H"),
        "Minute": converted_ticks.strftime("%M"),
        "Second": converted_ticks.strftime("%S"),
        "MiliSecond": str(int(converted_ticks.strftime("%f")) / 1000)
    }

def GetNTFSFileAttributes(bitArray):
    attributes = []
    n = 31 #Max index in bitArray
    if bitArray[n - 0] == "1":
        attributes.append("ReadOnly")
    if bitArray[n - 1] == "1":
        attributes.append("Hidden")
    if bitArray[n - 2] == "1":
        attributes.append("System")
    if bitArray[n - 5] == "1":
        attributes.append("Archive")
    if bitArray[n - 28] == "1":
        attributes.append("Directory")
    return attributes
    
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

#Convert two complement to integer
def twos_complement_to_integer(s):
    negative = (s[0] == '1')
    
    if negative:
        s = ''.join(['0' if c == '1' else '1' for c in s])
        s = bin(int(s, 2) + 1)[2:]
        
    return int('-' + s if negative else s, 2)