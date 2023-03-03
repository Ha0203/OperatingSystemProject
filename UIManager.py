from tkinter import *

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

# Item Information
itemInfo = Canvas(window, bg="#646E8F", height=550, width=400)
itemInfo.place(anchor=SE, x=800, y=600)

window.mainloop()