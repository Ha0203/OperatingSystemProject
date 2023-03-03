import os
import psutil
import platform
import datetime

# GET DIRECTORY SIZE NEEDS OPTIMIZED

def get_disk_partitions():
    partitionsList = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        partitionInfo = {
            "name": partition.device,
            "format": partition.fstype,
            "options": partition.opts
        }
        partitionsList.append(partitionInfo)
    return partitionsList

def get_creation_date(path_to_file):
    # Windows ctime is creation time
    if platform.system() == "Windows":
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            return stat.st_mtime

# *** NOT OPTIMIZED ***
def get_dir_size(path):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += get_dir_size(entry.path)
    return total

def get_dir_tree(startpath):
    dirTree = []

    # Walk through disk to get items
    for root, dirs, files in os.walk(startpath):
        # Skip null folder and os-created folder
        if os.path.basename(root) == "" or os.path.basename(root) == "System Volume Information":
            continue

        # Get folder level
        level = root.replace(startpath, "").count(os.sep)

        # Get folder creation time
        crTime = get_creation_date(root)
        dateCreated = datetime.datetime.fromtimestamp(crTime).strftime("%Y-%m-%d")
        timeCreated = datetime.datetime.fromtimestamp(crTime).strftime("%H:%M:%S")

        # Add folder to directory tree
        folder = {
            "type": "folder",
            "path": root,
            "level": level,
            "name": os.path.basename(root),
            "attributes": {
                "read": os.access(root, os.R_OK),
                "write": os.access(root, os.W_OK),
                "execute": os.access(root, os.X_OK)
            },
            "dateCreated": dateCreated,
            "timeCreated": timeCreated,
            "size": 0
        }  
        dirTree.append(folder)      

        # Get files in folder
        level += 1
        for f in files:
            # Create file path
            filePath = root + "\\" + f

            # Get file creation time
            crTime = get_creation_date(filePath)
            dateCreated = datetime.datetime.fromtimestamp(crTime).strftime("%Y-%m-%d")
            timeCreated = datetime.datetime.fromtimestamp(crTime).strftime("%H:%M:%S")

            # Add file to directory tree
            fileDict = {
                "type": "file",
                "path": filePath,
                "level": level,
                "name": f,
                "attributes": {
                    "read": os.access(filePath, os.R_OK),
                    "write": os.access(filePath, os.W_OK),
                    "execute": os.access(filePath, os.X_OK)
                },
                "dateCreated": dateCreated,
                "timeCreated": timeCreated,
                "size": os.path.getsize(filePath)
            }
            dirTree.append(fileDict)

    # Update directory size     *** NOT OPTIMIZED ***
    for item in dirTree:
        if item["type"] == "folder":
            item["size"] = get_dir_size(item["path"])

    # Return directory tree
    return dirTree

# Print functions
def print_disk_partitions(diskPartitions):
    fmt_str = "{:<8} {:<7} {:<7}"
    for partition in diskPartitions:
        print(fmt_str.format(partition["name"], partition["format"], partition["options"]))

def print_dir_tree(tree):
    for item in tree:
        indent = " " * 4 * (item["level"])
        print("{}{}".format(indent, item["name"]))

# Get disk partitions
diskPartitions = get_disk_partitions()
print_disk_partitions(diskPartitions)

# Create directory tree of partition E:\
diskHierarchy = get_dir_tree("E:\\")    # E:\\ is name of the partition 
print_dir_tree(diskHierarchy)