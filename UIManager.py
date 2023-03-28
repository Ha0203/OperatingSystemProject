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

def InformationHide():
    nameI["text"] = ""
    attributeI["text"] = ""
    timeCI["text"] = ""
    dateCI["text"] = ""
    sizeI["text"] = ""
    
def InformationDisplay(i):
    selected = dirTreeview.item(dirTreeview.focus())

    item = 0
    if currentPartition == 0 and len(diskHierarchyF) > 0:
        item = diskHierarchyF[0]
        for i in diskHierarchyF :
            if i["Name"] == selected["text"]:
                item = i
                break
    elif currentPartition == 1 and len(diskHierarchyN) > 0:
        item = diskHierarchyN[0]
        for i in diskHierarchyN:
            if i["Name"] == selected["text"]:
                item = i
                break

    nameI["text"] = item["Name"]
    attributeI["text"] = item["Attributes"]
    temp = item["TimeCreated"]
    timeCI["text"] = str(temp["Hour"]) + ":" + str(temp["Minute"]) + ":" + str(temp["Second"]) + "," + str(temp["MiliSecond"])
    temp = item["DateCreated"]
    dateCI["text"] = str(temp["Day"]) + "/" + str(temp["Month"]) + "/" + str(temp["Year"])
    sizeI["text"] = str(item["Size"]) + " bytes"

def TreeDel():
    for c in dirTreeview.get_children():
        dirTreeview.delete(c)

def FATBuild(partition):
    #Adding item to directory tree
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

    # select1["bg"] = "#19A7CE"
    # select2["bg"] = "#ffffff"
    currentPartition = 0
            
def NTFSBuild(partition):
    #Adding item to directory tree
    InformationHide()
    TreeDel()
    for item in partition["Hierarchy"]:
        dirTreeview.insert("", END, text=item["Name"], iid=item["ID"], open=False)
        
    count = 0    
    for item in partition["Hierarchy"]:
        if item["Parent"] >= 0 and item["ID"] != 5:
            dirTreeview.move(item["ID"], item["Parent"], count)
            count += 1

    # select2["bg"] = "#19A7CE"
    # select1["bg"] = "#ffffff"
    currentPartition = 1

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

# Treeview
dirTreeview = ttk.Treeview(itemList, height=24, show = "tree")
dirTreeview.column("#0", width = 390)
dirTreeview.heading('#0', text='FAT32', anchor=W)
dirTreeview.grid(row = 1, column = 0)

Cont2 = Frame(content, bg="#ffffff", height=550, width=450)
Cont2.grid(row = 0, column = 1, sticky = NSEW)
itemInfo = Frame(Cont2, bg="#ffffff", height=550, width=450)
itemInfo.grid(row = 1, column = 0, sticky = NSEW)

#Informations
blank = Label(Cont2, background = "#ffffff", width = 60, height = 0)
blank.grid(row = 0, column = 0 , sticky = NSEW)

nameL = Label(itemInfo, text = "Name:", bg = "#ffffff")
nameI = Label(itemInfo, bg = "#ffffff")
attributeL = Label(itemInfo, text = "Attributes:", bg = "#ffffff")
attributeI = Label(itemInfo, bg = "#ffffff")
timeCL = Label(itemInfo, text = "Time Created:", bg = "#ffffff")
timeCI = Label(itemInfo, bg = "#ffffff")
dateCL = Label(itemInfo, text = "Date Created:", bg = "#ffffff")
dateCI = Label(itemInfo, bg = "#ffffff")
sizeL = Label(itemInfo, text = "Size:", bg = "#ffffff")
sizeI = Label(itemInfo, bg = "#ffffff")

nameL.grid(row = 0, column = 0, sticky = W, pady = 5)
nameI.grid(row = 0, column = 1, sticky = W, pady = 5)
attributeL.grid(row = 1, column = 0, sticky = W, pady = 5)
attributeI.grid(row = 1, column = 1, sticky = W, pady = 5)
timeCL.grid(row = 2, column = 0, sticky = W, pady = 5)
timeCI.grid(row = 2, column = 1, sticky = W, pady = 5)
dateCL.grid(row = 3, column = 0, sticky = W, pady = 5)
dateCI.grid(row = 3, column = 1, sticky = W, pady = 5)
sizeL.grid(row = 4, column = 0, sticky = W, pady = 5)
sizeI.grid(row = 4, column = 1, sticky = W, pady = 5)

#Button Choice
buttonRow = 0
buttonIndex = 0
buttonWidth = 55
for drive in USBDrives:
    diskPartitions = DiskManager.ReadPhysicalDrive(drive.name, drive.BytesPerSector)
    diskPartitionsLength = len(diskPartitions)
    for partition in diskPartitions:
        if partition["Format"] == "NTFS":
            buttonList.append(Button(itemList, width = int(buttonWidth / 3) if (diskPartitionsLength - buttonRow * 3) % 3 == 0 else int(buttonWidth / 2) if (diskPartitionsLength - buttonRow * 3) % 3 == 2 else buttonWidth, text = partition["Format"], bg = "#ffffff", relief = SOLID, borderwidth = 1, command = lambda partition = partition: NTFSBuild(partition)))
        else:
            buttonList.append(Button(itemList, width = int(buttonWidth / 3) if (diskPartitionsLength - buttonRow * 3) % 3 == 0 else int(buttonWidth / 2) if (diskPartitionsLength - buttonRow * 3) % 3 == 2 else buttonWidth, text = partition["Format"], bg = "#ffffff", relief = SOLID, borderwidth = 1, command = lambda partition = partition: FATBuild(partition)))
        if buttonIndex % 3 == 0:
            buttonList[buttonIndex].grid(row = buttonRow, column = 0, sticky = W)
        elif buttonIndex % 3 == 1 and diskPartitionsLength - buttonIndex > 1:
            buttonList[buttonIndex].grid(row = buttonRow, column = 0, sticky = N)
        else:
            buttonList[buttonIndex].grid(row = buttonRow, column = 0, sticky = E)
            buttonRow += 1
        buttonIndex += 1

# select1 = Button(itemList, text = "FAT32", bg = '#ffffff', relief = SOLID, borderwidth = 1, command = FATBuild)
# select1.grid(row = 0, column = 0, sticky = W)
# select2 = Button(itemList, text = "NTFS", bg = '#ffffff', relief = SOLID, borderwidth = 1, command = NTFSBuild)
# select2.grid(row = 0, column = 0)

# Style
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="black", foreground="white", fieldbackground="black")
style.map('Treeview', background=[('selected', '#19A7CE')])
style.map('Treeview', bw=[('selected', 0)])
dirTreeview.bind('<ButtonRelease-1>', InformationDisplay)
currentPartition = 0
window.mainloop()