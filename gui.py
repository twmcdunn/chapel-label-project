# Trying to build a quick gui to draw boxes, if I have time and if it's helpful.
# Please feel free to build your own, if you can do it faster. I didn't want to make
# any promises that I could do this, because I'm not sure I have time...
"""
Controls:
left click to add box
right click drag to reposition box
hit enter to rename the box the mouse is over
right double click and drag to rename a bunch of boxes relative to a box that has been named manually
right and left arrows to change the status of the seat
    red = has a person in it
    green = empty
    blue = backback
press u to set the name of the seat at the upper left (used for autonaming all other seats)
press h to toggle show/hide boxes
press WASD to move all boxes at once
press o to open a new directory for data labeling
"""

import tkinter as tk
import tkinter.simpledialog
from PIL import ImageTk, Image
import sys
import json
import os
import math
from tkinter import filedialog



DATA_ROOT = ''#'trials/2_reolink2_wheaton_academy'#'trials/1_reolink1_wheaton_academy'

#build the window
window = tk.Tk()
window.title("Drawing Boxes")
screenWidth = window.winfo_screenwidth()
screenHeight = window.winfo_screenheight()
window.geometry(f"{screenWidth}x{screenHeight}+0+0")
window.columnconfigure(0,weight=1)
window.rowconfigure(0,weight=1)


imgDirectory = ''
imgFiles =''
imgPath = ''
scaleFactor = 1
unwrappedImage = None



def initialize():
    global imgFiles
    global imgPath
    global unwrappedImage
    global scaleFactor
    global SEAT_HEIGHT
    global SEAT_WIDTH
    global imgDirectory
    global newHeight
    imgDirectory = DATA_ROOT + '/images'
    imgFiles = os.listdir(imgDirectory)
    imgPath = imgDirectory + "/" + imgFiles[imageNum % len(imgFiles)]#r'C:\Users\timothymcdunn\Documents\Scripts\chapel-attendance2\cam-test\reolink1_6-1-25\Camera1_00_20250601140000.jpg'
    unwrappedImage = Image.open(imgPath)
    newHeight = window.winfo_screenheight() - 100
    scaleFactor = newHeight / unwrappedImage.height
    SEAT_WIDTH = 115#119
    SEAT_HEIGHT = 204#91#76
    SEAT_WIDTH *= scaleFactor
    SEAT_HEIGHT *= scaleFactor

imageNum = 0




# scale everythin based on image height vs screen height
SEAT_WIDTH = 115#119
SEAT_HEIGHT = 204#91#76
SEAT_WIDTH_HEIGHT_RATIO = 0

seatDims = {"SEAT_WIDTH": 155, "SEAT_HEIGHT": 204, "WIDTH_HEIGHT_RATIO": 0.757575758}


imgID = -1
img = -1

canvas = None
rect = -1

show_boxes = True

def canvas_bindings():
    global canvas
    global window
    canvas = tk.Canvas(window, width = 100, height=100)
    canvas.place(x=0,y=0)
    #global imgID
    #imgID = canvas.create_image(0,0,anchor=tk.NW,image=img)
    global rect
    rect = canvas.create_rectangle(0,0,SEAT_WIDTH,SEAT_HEIGHT,outline="red",width = 2)
    canvas.bind("<Motion>", mouse_movement)
    canvas.bind("<Button>", mouse_click)
    canvas.bind("<Double-3>", double_click)
    canvas.bind("<ButtonRelease>", mouse_release)
    window.bind("<Any-KeyPress>",key_press)

def updateImage(imgPath = None):
    global unwrappedImage
    if not imgPath is None:
        unwrappedImage = Image.open(imgPath)
    unwrappedImage = unwrappedImage.resize((int(unwrappedImage.width * scaleFactor), int(newHeight)))
    global img
    img = ImageTk.PhotoImage(unwrappedImage)
    global canvas
    if not canvas is None:
        canvas.destroy()
    canvas = tk.Canvas(window, width = img.width(), height=img.height())
    canvas.place(x=0,y=0)
    global imgID
    imgID = canvas.create_image(0,0,anchor=tk.NW,image=img)
    global rect
    rect = canvas.create_rectangle(0,0,SEAT_WIDTH,SEAT_HEIGHT,outline="red",width = 2)
    canvas.bind("<Motion>", mouse_movement)
    canvas.bind("<Button>", mouse_click)
    canvas.bind("<Double-3>", double_click)
    canvas.bind("<ButtonRelease>", mouse_release)
    window.bind("<Any-KeyPress>",key_press)

#initialize UI parameters

mx = -1
my = -1
selectedBox = -1
boxXOffset = -1
boxYOffset = -1
renameBounds = -1
upperLeftSeat = [0,0]
itemStatDictionary = {}
statusColorDictionary = {0:"red",
                         1:"green",
                         2:"blue"}

def loadSession():
    try:
        file = open(DATA_ROOT + '/gui_session.txt','r')
    except FileNotFoundError:
        return
    jsonString = file.read()
    jsonObj = json.loads(jsonString)
    deserialize_canvas(jsonObj)



def serialize_canvas():
    ids = filter(lambda a: a != imgID and a != rect and a != renameBounds, canvas.find_all())
    objects = []
    for item in ids:
        type = canvas.type(item)
        coords = canvas.coords(item)
        options = {} #canvas.itemconfig(item)
        
        optionsToDefine = ["text","fill","outline", "tags"]
        for opt in optionsToDefine:
            try:
                options[opt] = canvas.itemcget(item,opt)
            except Exception as ex:
                print(ex)
        objData = {
            "type": type,
            "coords": coords,
            "options":options,
            "id": item
        }

        

        objects.append(objData)

    jsonObj = {
        "canvasObjects": objects,
        "statDictionary": itemStatDictionary
    }
    return json.dumps(jsonObj)
    
def deserialize_canvas(data):
    jsonObj = data
    objects = jsonObj["canvasObjects"]
    idDictionary = {}
    deserializedIDDictionary = {}
    itemsToConfigure = []
    itemOptionsDictionary = {}
    for obj in objects:
            obj_type = obj["type"]
            coords = obj["coords"]
            options = obj["options"]
            serializedID = obj["id"]
            item = -1
            if obj_type == "rectangle":
                item = canvas.create_rectangle(*coords,**options)
            elif obj_type == "oval":
                item = canvas.create_oval(*coords,**options)
            elif obj_type == "line":
                item = canvas.create_line(*coords, **options)
            elif obj_type == "text":
                item = canvas.create_text(*coords, **options)
            itemsToConfigure.append(item)
            idDictionary[str(serializedID)] = str(item)
            deserializedIDDictionary[str(item)] = str(serializedID)
            itemOptionsDictionary[item] = options

    global itemStatDictionary
    itemStatDictionary = {}

    serializedStatDictionary = jsonObj["statDictionary"]

    for item in itemsToConfigure:
        serializedTags = list(canvas.gettags(item))

        #deserizalize tags
        for n in range(len(serializedTags)):
            try:
                deserializedValue = str(int(serializedTags[n]))
                serializedTags[n] = idDictionary[deserializedValue]
            except ValueError:
                pass
        deserializedTags = tuple(serializedTags)

        canvas.itemconfig(item, tags=deserializedTags)

        try:
            itemStatDictionary[item] = serializedStatDictionary[deserializedIDDictionary[str(item)]]
            canvas.itemconfig(item,outline = statusColorDictionary[itemStatDictionary[item]])
        except KeyError:
            pass
    #itemStatDictionary = jsonObj["statDictionary"]


def closest_box(x,y):
        ids = filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all())
        closest = -1
        bestdist = sys.maxsize
        for id in ids:
            coords = canvas.coords(id)
            dist = pow(pow(0.5*(coords[0] + coords[2]) - x,2) + pow(0.5*(coords[1]+coords[3]) - y,2), 0.5)
            if dist < bestdist:
                bestdist = dist
                closest = id
        return closest

def key_press(event):
    closest = closest_box(mx,my)
    if event.keysym == "BackSpace":
        for tag in canvas.gettags(closest):
            try:
                canvas.delete(int(tag))
            except ValueError:
                print("NOT A NUM, but that's ok")
        canvas.delete(closest)
    if event.keysym == "Right":
        itemStatDictionary[closest] = (itemStatDictionary[closest] + 1) % 3
        canvas.itemconfig(closest,outline = statusColorDictionary[itemStatDictionary[closest]])
    if event.keysym == "Left":
        itemStatDictionary[closest] = (itemStatDictionary[closest] - 1) % 3
        canvas.itemconfig(closest,outline = statusColorDictionary[itemStatDictionary[closest]])
    if event.keysym == "Return":
        orig = canvas.itemcget(int(canvas.gettags(closest)[0]),"text")
        name = tkinter.simpledialog.askstring("Manual Rename", "What would you like to rename this seat? (" + orig + ")")
        canvas.itemconfig(int(canvas.gettags(closest)[0]), text=name)
        canvas.addtag_withtag("manual", closest)
    if event.keysym == "u":
        xInChart = -1
        yInChart = -1
        refName = tkinter.simpledialog.askstring("Upper Left Reference", "What is the name of the seat in the upper left of this image?")
        for x in range(len(seatingChart)):
            if refName in seatingChart[x]:
                xInChart = x
                yInChart = seatingChart[x].index(refName)
                break
        global upperLeftSeat
        upperLeftSeat = [xInChart,yInChart]
    global SEAT_HEIGHT,SEAT_WIDTH, seatDims,scaleFactor
    if event.keysym == "equal":
        SEAT_HEIGHT += 2
        SEAT_WIDTH = int(round(SEAT_HEIGHT * SEAT_WIDTH_HEIGHT_RATIO))
        ids = filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all())
        for id in ids:
            coords = canvas.coords(id)
            aveX = sum(coords[::2]) / 2
            aveY = sum(coords[1::2]) / 2
            canvas.coords(id, int(round(aveX - SEAT_WIDTH / 2)),int(round(aveY - SEAT_HEIGHT / 2)),int(round(aveX + SEAT_WIDTH / 2)),int(round(aveY + SEAT_HEIGHT / 2)))
        seatDims["SEAT_WIDTH"] = int(round(SEAT_WIDTH / scaleFactor))
        seatDims["SEAT_HEIGHT"] = int(round(SEAT_HEIGHT / scaleFactor))
        with open("seatDims.json", "w") as f:
            f.write(json.dumps(seatDims))
    if event.keysym == "minus":
        SEAT_HEIGHT -= 2
        SEAT_WIDTH = int(round(SEAT_HEIGHT * SEAT_WIDTH_HEIGHT_RATIO))
        ids = filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all())
        for id in ids:
            coords = canvas.coords(id)
            aveX = sum(coords[::2]) / 2
            aveY = sum(coords[1::2]) / 2
            canvas.coords(id, int(round(aveX - SEAT_WIDTH / 2)),int(round(aveY - SEAT_HEIGHT / 2)),int(round(aveX + SEAT_WIDTH / 2)),int(round(aveY + SEAT_HEIGHT/ 2)))
        seatDims["SEAT_WIDTH"] = int(round(SEAT_WIDTH / scaleFactor))
        seatDims["SEAT_HEIGHT"] = int(round(SEAT_HEIGHT / scaleFactor))
        with open("seatDims.json", "w") as f:
            f.write(json.dumps(seatDims))
    if event.keysym == "w":
        ids =  filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all())
        for id in ids:
            coords = canvas.coords(id)
            canvas.coords(id, coords[0],coords[1] - 1, coords[2],coords[3] - 1)
            labelIds = filter(lambda a: 'label' in canvas.gettags(a) and str(id) in canvas.gettags(a), canvas.find_all())
            for lid in labelIds:
                coords = canvas.coords(lid)
                if canvas.type(lid) == "text":
                    canvas.coords(lid, coords[0],coords[1] - 1)
                else:
                    canvas.coords(lid, coords[0],coords[1] - 1, coords[2],coords[3] - 1)
    if event.keysym == "s":
        ids =  filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all())
        for id in ids:
            coords = canvas.coords(id)
            canvas.coords(id, coords[0],coords[1] + 1, coords[2],coords[3] + 1)
            labelIds = filter(lambda a: 'label' in canvas.gettags(a) and str(id) in canvas.gettags(a), canvas.find_all())
            for lid in labelIds:
                coords = canvas.coords(lid)
                if canvas.type(lid) == "text":
                    canvas.coords(lid, coords[0],coords[1] + 1)
                else:
                    canvas.coords(lid, coords[0],coords[1] + 1, coords[2],coords[3] + 1)
    if event.keysym == "o":
        file_open()

    global imageNum
    global imgPath
    if event.keysym == "Up":
        imageNum += 1
        imgPath = imgDirectory + "/" + imgFiles[imageNum % len(imgFiles)]
        updateImage(imgPath)
        loadSession()
    if event.keysym == "Down":
        imageNum -= 1
        imgPath = imgDirectory + "/" + imgFiles[imageNum % len(imgFiles)]
        updateImage(imgPath)
        loadSession()
    if event.keysym == "h":
        global show_boxes
        if show_boxes:
            show_boxes = False
            imgPath = imgDirectory + "/" + imgFiles[imageNum % len(imgFiles)]
            updateImage(imgPath)
        else:
            show_boxes = True
            imgPath = imgDirectory + "/" + imgFiles[imageNum % len(imgFiles)]
            updateImage(imgPath)
            loadSession()
    
    
    autoname_seats()


def mouse_movement(event):
    global mx
    global my
    global selectedBox
    mx = event.x
    my = event.y
    canvas.coords(rect, event.x, event.y, event.x+SEAT_WIDTH, event.y+SEAT_HEIGHT)
    if event.state & 0x0400 != 0:#right
        if renameBounds != -1:
            coords = canvas.coords(selectedBox)
            canvas.coords(renameBounds,int((coords[0] + coords[2])/2),int((coords[1] + coords[3])/2),event.x,event.y)
            recolor()
        else:
            canvas.coords(selectedBox, event.x + boxXOffset, event.y + boxYOffset, event.x + boxXOffset +SEAT_WIDTH, event.y + boxYOffset +SEAT_HEIGHT)
            
            canvas.coords(int(canvas.gettags(selectedBox)[1]),
                        boxXOffset + event.x + SEAT_WIDTH // 2 - 20, boxYOffset + event.y + SEAT_HEIGHT // 2 - 7,
                        boxXOffset + event.x + SEAT_WIDTH // 2 + 20, boxYOffset + event.y + SEAT_HEIGHT // 2 + 7)
            canvas.coords(int(canvas.gettags(selectedBox)[0]),
                        boxXOffset + event.x + SEAT_WIDTH // 2, boxYOffset + event.y + SEAT_HEIGHT // 2)
            
    if event.state & 0x0100 != 0:#left
       print("m") 

def mouse_release(event):
    autoname_seats()
    global renameBounds
    if renameBounds != -1:#left
        autorename(selectedBox, canvas.coords(renameBounds))
        canvas.delete(renameBounds)
        renameBounds = -1
    recolor()

def mouse_click(event):
    #print(event.num)
    global selectedBox
    if event.num == 1:
        print("RC")
        #canvas.raise(newRect)
        newRect = canvas.create_rectangle(event.x,event.y,event.x+SEAT_WIDTH,event.y+SEAT_HEIGHT,outline="red",width = 2)
        global itemStatDictionary
        itemStatDictionary[newRect] = 0
        labelBg = canvas.create_rectangle(event.x + SEAT_WIDTH // 2 - 20,event.y + SEAT_HEIGHT // 2 - 7, event.x + SEAT_WIDTH // 2 + 20,event.y + SEAT_HEIGHT // 2 + 7, fill='white',tags=(str(newRect),'label'))
        label = canvas.create_text(event.x + SEAT_WIDTH // 2,event.y + SEAT_HEIGHT // 2,text='',fill='red',tags=(str(newRect),'label'))
        canvas.addtag_withtag(str(label),newRect)
        canvas.addtag_withtag(str(labelBg),newRect)

        orig = canvas.itemcget(int(canvas.gettags(newRect)[0]),"text")
        name = tkinter.simpledialog.askstring("Manual Rename", "What would you like to rename this seat? (" + orig + ")")
        canvas.itemconfig(int(canvas.gettags(newRect)[0]), text=name)
        canvas.addtag_withtag("manual", newRect)

        autoname_seats()
    if event.num == 3:#right click
        selectedBox = closest_box(event.x,event.y)
        global boxXOffset
        global boxYOffset
        coords = canvas.coords(selectedBox)
        boxXOffset = coords[0] - event.x
        boxYOffset = coords[1] - event.y

""" 
def mouse_drag(event):
    if event.state & 0x0400 != 0:
         canvas.itemconfig(selectedBox, x0 = event.x, y0 = event.y)
         canvas.itemconfig(int(canvas.gettags(selectedBox)[1]),x0=event.x + SEAT_WIDTH // 2 - 20,y0=event.y + SEAT_HEIGHT // 2 - 7)
         canvas.itemconfig(int(canvas.gettags(selectedBox)[0]),x=event.x + SEAT_WIDTH // 2,y=event.y + SEAT_HEIGHT // 2)
 """
def recolor():
    ids = filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all())
    for box in ids:
        canvas.itemconfig(box, outline = statusColorDictionary[itemStatDictionary[int(box)]])
    if renameBounds != -1:
        bounds = canvas.coords(renameBounds)
        boxes = list(filter(lambda a: 
                            a != imgID and a != rect and ('label' not in canvas.gettags(a))
                            and (
                                boxOverlaps(a, bounds)
                            ), 
                        canvas.find_all()))
        for box in boxes:
            canvas.itemconfig(int(box), outline = "black")

def double_click(event):
    print("DBL")
    #if event.state & 0x0400 != 0:#right
    global renameBounds
    global selectedBox
    selectedBox = closest_box(event.x,event.y)
    coords = canvas.coords(selectedBox)
    renameBounds = canvas.create_rectangle(int((coords[0] + coords[2])/2),int((coords[1] + coords[3])/2),event.x,event.y, outline="black",tags="label")

def generate_seating_chart():
    return testSeatingChart()
    seatingChart = []
    outerMost = [18,20,21,21,22,22,23,23,24,26,27] + ([28] * 24) + ([24] * 9)
    basicAlph = ['a','b','c','d','e','f','g','h','j','k','l','m','n','p','q','r','s']
    alphabet1 = basicAlph + []
    alphabet2 = []
    alphabet3 = []
    for a in basicAlph:
        alphabet2.append(a * 2)
    for n in range(1,11):
        alphabet3.append(basicAlph[n])
    

    for x in range(28,0,-1):
        column = []
        for y in range(len(alphabet1)):
            section = 1
            row = alphabet1[y]
            seat = x
            name = str(section) + str(row) + str(seat)
            #seatingChart[x][y] = name
            column.append(name)
        for y in range(len(alphabet2)):
            section = 2
            row = alphabet2[y]
            seat = x
            name = str(section) + str(row) + str(seat)
            #seatingChart[x][y] = name
            column.append(name)
        for y in range(len(alphabet3)):
            section = 5
            row = alphabet3[y]
            seat = x
            name = str(section) + str(row) + str(seat)
            #seatingChart[x][y] = name
            column.append(name)
        
        column.reverse()

        seatingChart.append(column)

    for x in range(1,29,1):
        column = []
        for y in range(len(alphabet1)):
            section = 3
            row = alphabet1[y]
            seat = x
            name = str(section) + str(row) + str(seat)
            #seatingChart[x][y] = name
            column.append(name)
        for y in range(len(alphabet2)):
            section = 4
            row = alphabet2[y]
            seat = x
            name = str(section) + str(row) + str(seat)
            #seatingChart[x][y] = name
            column.append(name)
        for y in range(len(alphabet3)):
            section = 6
            row = alphabet3[y]
            seat = x
            name = str(section) + str(row) + str(seat)
            #seatingChart[x][y] = name
            column.append(name)
        column.reverse()
        seatingChart.append(column)
        
    seatingChart.reverse()
    with open("seatingchart.csv", "w") as sc:
        for c in seatingChart:
            for s in c:
                sc.write(str(s) + ";")
        sc.write("\n")
    return seatingChart

def testSeatingChart():
    chart = []
    for x in range(500):
        row = []
        for y in range(500):
            row.append(str(x) + "-" + str(y))
        chart.append(row)
    return chart



def interpolate_grid(unsortedIds):
    ##columns are called rows here, just to confuse people ;)
    fractOfSeat = 0.75
    #what fraction of a seat away can an x choordinate be and still be considered the same column?

    rows = []

    while len(unsortedIds) > 0:
        row = [unsortedIds[0]]
        myX = canvas.coords(unsortedIds[0])[0]
        
        for n in range(1,len(unsortedIds)):
            if abs(canvas.coords(unsortedIds[n])[0] - myX) < (SEAT_WIDTH * fractOfSeat):
                row.append(unsortedIds[n])
        row = sorted(row, key= lambda a: canvas.coords(a)[1])
        rows.append(row)
        unsortedIds = list(filter(lambda a: a not in row, unsortedIds))

    rows = sorted(rows, key = lambda a: canvas.coords(a[0])[0])

    minY = sys.maxsize
    for row in rows:
        minY = min(canvas.coords(row[0])[1],minY)
    return rows, minY

def interpolate_grid1(unsortedIds):
    fractOfSeat = 1
    #what fraction of a seat away can an y choordinate be and still be considered the same row?

    rows = []

    while len(unsortedIds) > 0:
        row = [unsortedIds[0]]
        myY = canvas.coords(unsortedIds[0])[1]
        
        for n in range(1,len(unsortedIds)):
            if abs(canvas.coords(unsortedIds[n])[1] - myY) < (SEAT_HEIGHT * fractOfSeat):
                row.append(unsortedIds[n])
        row = sorted(row, key= lambda a: canvas.coords(a)[0])
        rows.append(row)
        unsortedIds = list(filter(lambda a: a not in row, unsortedIds))

    rows = sorted(rows, key = lambda a: canvas.coords(a[0])[1])

    minX = sys.maxsize
    for row in rows:
        minX = min(canvas.coords(row[0])[0],minX)

    # Find the maximum row length
    max_columns = max(len(row) for row in rows) if rows else 0

    columns = []
    for x in range(max_columns):
        column = []
        for y in range(len(rows)):
            if x < len(rows[y]):  # Check if this row has a seat at this column
                column.append(rows[y][x])
            # Skip seats that don't exist rather than adding None
        if column:  # Only add non-empty columns
            columns.append(column)

    return columns, 0

def interpolate_grid_sequential_build(unsortedIds):
    y_tollerance = 0.5 * SEAT_HEIGHT
    x_tollerance = 1.3 * SEAT_WIDTH
    
    rows = []

    while len(unsortedIds) > 0:
        sorted_by_x = sorted(unsortedIds, key = lambda a: canvas.coords(a)[0])
        
        seed_seat = sorted_by_x[0]
        row = [seed_seat]
        for n in range(1, len(sorted_by_x)):
            candidate_seat = sorted_by_x[n]
            if abs(canvas.coords(candidate_seat)[0] - canvas.coords(row[len(row) - 1])[0]) > x_tollerance:
                break ##no more seats within range (this logic means rows must be contiguous, should be easy to improve)
            if abs(canvas.coords(candidate_seat)[1] - canvas.coords(row[len(row) - 1])[1]) <= y_tollerance:
                row.append(candidate_seat)
        unsortedIds = list(filter(lambda a: a not in row, unsortedIds))
        rows.append(row)

    rows = sorted(rows, key = lambda a: canvas.coords(a[0])[1])

     # Find the maximum row length
    max_columns = max(len(row) for row in rows) if rows else 0

    columns = []
    for x in range(max_columns):
        column = []
        for y in range(len(rows)):
            if x < len(rows[y]):  # Check if this row has a seat at this column
                column.append(rows[y][x])
            # Skip seats that don't exist rather than adding None
        if column:  # Only add non-empty columns
            columns.append(column)

    return columns, 0

autoname_running = False

def autoname_seats():
    if not show_boxes:
        return
    global autoname_running
    if autoname_running:
        return
    
    autoname_running = True

    unsortedIds = list(filter(lambda a: a != imgID and a != rect and ('label' not in canvas.gettags(a)), canvas.find_all()))
    rows, minY = interpolate_grid_sequential_build(unsortedIds)

    file = open(DATA_ROOT + "/seats.csv","w")
    targets = open(DATA_ROOT + "/targets.csv","w")
    backpacks = open(DATA_ROOT + "/backpacks.csv","w")
    for x in range(len(rows)):
        for y in range(len(rows[x])):
            #yOffset = int(int(canvas.coords(rows[x][0])[1] - minY) // SEAT_HEIGHT)##how far down is this whole column shifted relative to the highest seat recorded
            yOffset = 0
            name = seatingChart[x+upperLeftSeat[0]][y+upperLeftSeat[1] + yOffset]
            if "manual" not in canvas.gettags(rows[x][y]):
                canvas.itemconfig(int(canvas.gettags(rows[x][y])[0]),text=name)
            else:
                name = canvas.itemcget(int(canvas.gettags(rows[x][y])[0]),"text")
            coords = canvas.coords(int(rows[x][y]))

            file.write(str(round(coords[0] / scaleFactor)) + "," + str(round(coords[1] / scaleFactor)) + "," + name + "\n")
            if itemStatDictionary[rows[x][y]] == 1 or itemStatDictionary[rows[x][y]] == 2:
                targets.write(str(round(coords[0] / scaleFactor)) + "," + str(round(coords[1] / scaleFactor)) + "," + name + "\n")
            if itemStatDictionary[rows[x][y]] == 2:
                backpacks.write(str(round(coords[0] / scaleFactor)) + "," + str(round(coords[1] / scaleFactor)) + "," + name + "\n")
    file.close()
    targets.close()
    backpacks.close()
    file = open(DATA_ROOT + "/gui_session.txt", "w")
    file.write(serialize_canvas())
    file.close()

    autoname_running = False
    
def boxOverlaps(boxId, bounds):
    coords = canvas.coords(boxId)
    coords.append(coords[0])
    coords.append(coords[3])
    coords.append(coords[2])
    coords.append(coords[1])
    for n in range(4):
        point = (coords[n*2],coords[n*2 + 1])
        if (point[0] >= bounds[0] and point[0] <= bounds[2] and 
            point[1] >= bounds[1] and point[1] <= bounds[3]):
            return True
    return False

def autorename(reference, bounds):
    print()
    boxes = list(filter(lambda a: 
                           a != imgID and a != rect and ('label' not in canvas.gettags(a))
                           and (
                               boxOverlaps(a, bounds)
                           ), 
                        canvas.find_all()))
    
    rows, minY = interpolate_grid(boxes)
    xInInterp = -1
    yInInterp = -1
    for x in range(len(rows)):
        if reference in rows[x]:
            xInInterp = x
            yInInterp = rows[x].index(reference)
            break
    
    xInChart = -1
    yInChart = -1
    refName = canvas.itemcget(int(canvas.gettags(reference)[0]),"text")
    for x in range(len(seatingChart)):
        if refName in seatingChart[x]:
            xInChart = x
            yInChart = seatingChart[x].index(refName)
            break
    
    myUpperLeftSeat = [xInChart - xInInterp, yInChart - yInInterp]

    for x in range(len(rows)):
        for y in range(len(rows[x])):
            yOffset = int(int(canvas.coords(rows[x][0])[1] - minY) // SEAT_HEIGHT)
            name = seatingChart[x+myUpperLeftSeat[0]][y+myUpperLeftSeat[1] + yOffset]
            canvas.itemconfig(int(canvas.gettags(rows[x][y])[0]),text=name)
            canvas.addtag_withtag("manual",rows[x][y])

def file_open():
    global DATA_ROOT
    DATA_ROOT = filedialog.askdirectory(
    title="Open a camera data folder")
    initialize()
    updateImage()
    loadSession()
    
    
# Create a menu bar
menu_bar = tk.Menu(window)

# Create a File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=file_open)
#file_menu.add_separator()
#file_menu.add_command(label="Exit", command=exit_app)

# Add the File menu to the menu bar
menu_bar.add_cascade(label="File", menu=file_menu)

window.config(menu=menu_bar)

seatingChart = generate_seating_chart()
# updateImage()
# loadSession()
canvas_bindings()
window.mainloop()
