from tkinter import *
from tkinter import ttk
import DiskManager

def TreeDel():
    for c in dirTreeview.get_children():
        dirTreeview.delete(c)

def FATBuild():
    #Adding item to directory tree
    TreeDel()
    count = 0
    for item in diskHierarchyF:
        dirTreeview.insert("", END, text=item["Name"], iid=count, open=False)
        item["ID"] = count
        count += 1
        
    aCount = []
    i = 0
    while i < count:
        aCount.append(0)
        i += 1
        
    for item in diskHierarchyF:
        if item["Parent"] >= 0:
            dirTreeview.move(item["ID"], item["Parent"], aCount[item["Parent"]])
            
def NTFSBuild():
    #Adding item to directory tree
    TreeDel()
    count = 0
    for item in diskHierarchyN:
        dirTreeview.insert("", END, text=item["Name"], iid=count, open=False)
        count += 1
        
    aCount = []
    i = 0
    while i < count:
        aCount.append(0)
        i += 1
        
    for item in diskHierarchyN:
        if item["Parent"] >= 0:
            dirTreeview.move(item["ID"], item["Parent"], aCount[item["Parent"]])
# Data
diskPartitions = DiskManager.diskPartitions
diskHierarchyF = []
diskHierarchyN = []
c = 0
for partition in diskPartitions:
    if partition["Format"] == "FAT32":
        diskHierarchyF = partition["Hierarchy"]
        c += 1
    elif partition["Format"] == "NTFS":
        diskHierarchyN = partition[diskHierarchyN]
        c += 1
    if c == 2:
        break

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
select1 = Button(itemList, text = "FAT32", bg = '#ffffff', relief = SOLID, borderwidth = 0, command = FATBuild)
select1.grid(row = 0, column = 0, sticky = W, pady = 2)
select2 = Button(itemList, text = "NTFS", bg = '#ffffff', relief = SOLID, borderwidth = 0, command = NTFSBuild)
select2.grid(row = 0, column = 0)
# Treeview
dirTreeview = ttk.Treeview(itemList, height=24)
dirTreeview.column("#0", width = 390)
dirTreeview.heading('#0', text='FAT32', anchor=W)
dirTreeview.grid(row = 1, column = 0)

FATBuild()

itemInfo = Canvas(content, bg="#646E8F", height=550, width=450)
itemInfo.grid(row = 0, column = 1, sticky = NE)

# Style
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#323232", foreground="white", fieldbackground="#323232")


window.mainloop()