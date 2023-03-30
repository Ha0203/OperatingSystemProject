from tkinter import *
from tkinter import ttk
import DiskManager

# Data
USBDrives = DiskManager.GetUSBDrive()
USBDrivesLength = len(USBDrives)

diskPartitions = []
diskPartitionsLength = 0

driveButtonList = []
buttonList = []

def SelectedButtonFill(idx):
    global buttonList
    for i in buttonList:
        i["bg"] = "#ffffff"
    
    buttonList[idx]["bg"] = "#19A7CE"

def InformationHide():
    nameI["text"] = ""
    attributeI["text"] = ""
    timeCI["text"] = ""
    dateCI["text"] = ""
    sizeI["text"] = ""
    
def InformationDisplay(e):
    InformationHide()
    global currentPartition
    selected = dirTreeview.item(dirTreeview.focus())
        
    item = {
        "Name": "NULL",
        "Attributes": "NULL",
        "TimeCreated": {
            "Hour": 0,
            "Minute": 0,
            "Second": 0,
            "MiliSecond": 0
        },
        "DateCreated": {
            "Day": 0,
            "Month": 0,
            "Year": 0
        },
        "Size": 0
    }

    for i in currentPartition["Hierarchy"]:
        if i["Name"] == selected["text"]:
            item = i
            break

    i = 0
    end = 50
    limit = 0
    while end < len(item["Name"]) and limit < 5:
        nameI["text"] += item["Name"][i : end] + "\n"
        limit += 1
        i += 50
        end += 50
    if end > len(item["Name"]) and limit < 5:
        nameI["text"] += item["Name"][i :] + "\n"
        
    attributeI["text"] = item["Attributes"]
    temp = item["TimeCreated"]
    timeCI["text"] = str(temp["Hour"]) + ":" + str(temp["Minute"]) + ":" + str(temp["Second"])
    temp = item["DateCreated"]
    dateCI["text"] = str(temp["Day"]) + "/" + str(temp["Month"]) + "/" + str(temp["Year"])
    sizeI["text"] = str(item["Size"]) + " bytes"

def TreeDel():
    for c in dirTreeview.get_children():
        dirTreeview.delete(c)

def FATBuild(partition, idx):
    #Adding item to directory tree
    global currentPartition
    InformationHide()
    TreeDel()
    count = 0
    for item in partition["Hierarchy"]:
        dirTreeview.insert("", END, text=item["Name"], iid=count, open=False)
        item["ID"] = count
        count += 1
        
    count = 0
    for item in partition["Hierarchy"]:
        if item["Parent"] >= 0:
            dirTreeview.move(item["ID"], item["Parent"], count)
            count += 1

    currentPartition = partition
    SelectedButtonFill(idx)
            
def NTFSBuild(partition, idx):
    #Adding item to directory tree
    global currentPartition 
    InformationHide()
    TreeDel()
    for item in partition["Hierarchy"]:
        dirTreeview.insert("", END, text=item["Name"], iid=item["ID"], open=False)
        
    count = 0    
    for item in partition["Hierarchy"]:
        if item["Parent"] >= 0 and item["ID"] != 5:
            dirTreeview.move(item["ID"], item["Parent"], count)
            count += 1

    currentPartition = partition
    SelectedButtonFill(idx)

# GUI window
window = Tk()

window.title("Disk Check")
window.configure(width=800, height=600, bg="#19A7CE")
windowName = Label(window, text="DISK CHECK", fg="white", font=("MS Serif", 50, "bold"), bg="#19A7CE")
windowName.grid(row = 0, column = 0, padx = 200)
window.resizable(False, False)

#Content
content = Canvas(window, bg="#ffffff", height=550, width=400)
content.grid(row = 1, column = 0, sticky = NW)

# Items List
itemList = Canvas(content, bg="#ffffff", height=550, width=400)
itemList.grid(row = 0, column = 0, sticky = NW)

#Button Choice
buttonRow = 0
buttonIndex = 0
buttonWidth = 55
diskPartitions = []
diskPartitionsLength = 0
for drive in USBDrives:
    partitions = DiskManager.ReadPhysicalDrive(drive.name, drive.BytesPerSector)
    diskPartitions.append(partitions)
    
for partitions in diskPartitions:
    diskPartitionsLength += len(partitions)
    
for partitions in diskPartitions:
    for partition in partitions:
        currentPartition = partition
        if partition["Format"] == "NTFS":
            buttonList.append(Button(itemList, width = int(buttonWidth / 3) if (diskPartitionsLength - buttonRow * 3) > 3 or (diskPartitionsLength - buttonRow * 3) % 3 == 0 else int(buttonWidth / 2) if (diskPartitionsLength - buttonRow * 3) % 3 == 2 else buttonWidth, text = partition["Format"] + " " + str(buttonIndex + 1), bg = "#ffffff", relief = SOLID, borderwidth = 1, command = lambda partition = partition, buttonIndex = buttonIndex: NTFSBuild(partition, buttonIndex)))
        else:
            buttonList.append(Button(itemList, width = int(buttonWidth / 3) if (diskPartitionsLength - buttonRow * 3) > 3 or (diskPartitionsLength - buttonRow * 3) % 3 == 0 else int(buttonWidth / 2) if (diskPartitionsLength - buttonRow * 3) % 3 == 2 else buttonWidth, text = partition["Format"] + " " + str(buttonIndex + 1), bg = "#ffffff", relief = SOLID, borderwidth = 1, command = lambda partition = partition, buttonIndex = buttonIndex: FATBuild(partition, buttonIndex)))
        if buttonIndex % 3 == 0:
            buttonList[buttonIndex].grid(row = buttonRow, column = 0, sticky = W)
        elif buttonIndex % 3 == 1 and diskPartitionsLength - buttonIndex > 1:
            buttonList[buttonIndex].grid(row = buttonRow, column = 0)
        else:
            buttonList[buttonIndex].grid(row = buttonRow, column = 0, sticky = E)
            buttonRow += 1
        buttonIndex += 1
if len(buttonList) % 3 == 1:
    buttonRow += 1

# Treeview
dirTreeview = ttk.Treeview(itemList, height=24, show = "tree")
dirTreeview.column("#0", width = 390)
dirTreeview.heading('#0', text='FAT32', anchor=W)
dirTreeview.grid(row = buttonRow, column = 0)

Cont2 = Frame(content, bg="#ffffff", height=550, width=450)
Cont2.grid(row = 0, column = 1, sticky = NSEW)
itemInfo = Frame(Cont2, bg="#ffffff", height=550, width=450)
itemInfo.grid(row = 1, column = 0, sticky = NSEW)

#Informations
blank = Label(Cont2, background = "#ffffff", width = 60, height = 0)
blank.grid(row = 0, column = 0 , sticky = NSEW)

nameL = Label(itemInfo, text = "Name:", bg = "#ffffff")
nameI = Label(itemInfo, bg = "#ffffff", anchor = "w", justify = LEFT)
attributeL = Label(itemInfo, text = "Attributes:", bg = "#ffffff")
attributeI = Label(itemInfo, bg = "#ffffff", anchor = "w", justify = LEFT)
timeCL = Label(itemInfo, text = "Time Created:", bg = "#ffffff")
timeCI = Label(itemInfo, bg = "#ffffff", anchor = "w", justify = LEFT)
dateCL = Label(itemInfo, text = "Date Created:", bg = "#ffffff")
dateCI = Label(itemInfo, bg = "#ffffff", anchor = "w", justify = LEFT)
sizeL = Label(itemInfo, text = "Size:", bg = "#ffffff")
sizeI = Label(itemInfo, bg = "#ffffff", anchor = "w", justify = LEFT)

nameL.grid(row = 0, column = 0, sticky = W, pady = 5)
nameI.grid(row = 0, column = 1, sticky = NSEW, pady = 5)
attributeL.grid(row = 3, column = 0, sticky = W, pady = 5)
attributeI.grid(row = 3, column = 1, sticky = NSEW, pady = 5)
timeCL.grid(row = 4, column = 0, sticky = W, pady = 5)
timeCI.grid(row = 4, column = 1, sticky = NSEW, pady = 5)
dateCL.grid(row = 5, column = 0, sticky = W, pady = 5)
dateCI.grid(row = 5, column = 1, sticky = NSEW, pady = 5)
sizeL.grid(row = 6, column = 0, sticky = W, pady = 5)
sizeI.grid(row = 6, column = 1, sticky = NSEW, pady = 5)

# Style
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#d4e0ff", foreground="white", fieldbackground="#d4e0ff")
style.map('Treeview', background=[('selected', '#19A7CE')])
style.map('Treeview', bw=[('selected', 0)])
dirTreeview.bind('<ButtonRelease-1>', InformationDisplay)
#Scrollbar
# Constructing vertical scrollbar
# with treeview
verscrlbar = Scrollbar(itemList,
                           orient ="vertical",
                           command = dirTreeview.yview,
                           activebackground = "#19A7CE",
                           bg = "#ffffff",
                           borderwidth = 50,
                           elementborderwidth = 50,
                           highlightbackground = "#ffffff",
                           highlightcolor = "#19A7CE",
                           troughcolor = "#ffffff",
                           width = 12,
                           takefocus = 1)
 
# Calling pack method w.r.to vertical
# scrollbar
verscrlbar.grid(row = buttonRow, column = 1, sticky = 'ns')
 
# Configuring treeview
dirTreeview.configure(yscrollcommand = verscrlbar.set)

window.mainloop()