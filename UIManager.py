from tkinter import *
from tkinter import ttk
import DiskManager

diskHierarchy = []

# GUI window
window = Tk()

window.title("Disk Check")

window.configure(width=800, height=600, bg="#704684")

windowName = Label(window, text="DISK CHECK", fg="black", font=(50), bg="#704684")
windowName.place(anchor=N, x=400, y=10)

window.resizable(False, False)

# Items List
itemList = Canvas(window, bg="#323232", height=550, width=400)
itemList.place(anchor=SW, x=0, y=600)

# Treeview
dirTreeview = ttk.Treeview(itemList, height=24)
dirTreeview.column("#0", width=390)
dirTreeview.heading('#0', text='E:\\', anchor=W)

# Adding item to directory tree
idCount = 0
for item in diskHierarchy:
    if item["parent"] < 0:
        dirTreeview.insert("", END, text=item["name"], iid=idCount, open=False)
    else:
        dirTreeview.insert(item["parent"], END, text=item["name"], iid=idCount, open=False)
    idCount += 1

dirTreeview.place(anchor=NW, x=2, y=43)

# Item Information
itemInfo = Canvas(window, bg="#646E8F", height=550, width=400)
itemInfo.place(anchor=SE, x=800, y=600)

# Style
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#323232", foreground="white", fieldbackground="#323232")

window.mainloop()