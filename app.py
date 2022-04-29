#
# File: app.py
# Date: 04/28/2022
# Author: Quinn Hogue
# Purpose: Creates and controls the GUI for the robotic arm control.
# Contacting: If you are an Etown student please talk to the one of the Engineering Faculty. 
# They most likely can get you my contact information. 

# Imports
from threading import Thread
import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Union
import RoboticArmFunctions


# Variable for Data Storage File
data_file = "robo.json"

# Variables for Setting Page
axis1_1_address, axis2_1_address, axis2_2_address, axis3_1_address, axis4_1_address = (
    14,
    15,
    16,
    17,
    18,
)
axis1_1_minang, axis2_1_minang, axis2_2_minang, axis3_1_minang, axis4_1_minang = (
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
)
axis1_1_maxang, axis2_1_maxang, axis2_2_maxang, axis3_1_maxang, axis4_1_maxang = (
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
)


class AsyncControl(Thread):
    def __init__(
        self,
        axis_curval_list: "list[tk.StringVar]",
        axis_setval_list: "list[tk.StringVar]",
        status: "list[tk.BooleanVar]", 
        stop_text: "list[tk.StringVar]"
    ):
        super().__init__()
        self.axis_curval_list = axis_curval_list
        self.axis_setval_list = axis_setval_list
        self.status = status
        self.stop_text = stop_text

    def run(self):
        RoboticArmFunctions.ctrlLoop(self.axis_curval_list, self.axis_setval_list, self.status, self.stop_text)



class PageTwoStartUp(Thread):
    def __init__(self, axis_curval_list, axis_setval_list):
        super().__init__()
        self.axis_curval_list = axis_curval_list
        self.axis_setval_list = axis_setval_list

    def run(self):
        RoboticArmFunctions.updateCurVal(self.axis_curval_list)
        for i in range(0, 4):
            self.axis_setval_list[i].set(self.axis_curval_list[i].get())
        RoboticArmFunctions.gripDeactivate()


class GripperControl(Thread):
    def __init__(self, state=str()):
        super().__init__()
        self.state = state

    def run(self):
        if self.state == "Open":
            RoboticArmFunctions.gripDeactivate()
        elif self.state == "Close":
            RoboticArmFunctions.gripActivate()


class ZeroAxisPosition(Thread):
    def __init__(self, axisNum, axis_curval_list, axis_setval_list):
        super().__init__()
        self.axis_curval_list = axis_curval_list
        self.axis_setval_list = axis_setval_list
        self.axisNum = axisNum

    def run(self):
        RoboticArmFunctions.set_current_position(
            self.axisNum, 0, self.axis_setval_list, self.axis_curval_list
        )
        

class LiveAxisControl(Thread):
    def __init__(
        self,
        axis_curval_list: "list[tk.StringVar]",
        axis_setval_list: "list[tk.StringVar]",
        status: "list[tk.BooleanVar]", 
        stop_text: "list[tk.StringVar]"
    ):
        super().__init__()
        self.axis_curval_list = axis_curval_list
        self.axis_setval_list = axis_setval_list
        self.status = status
        self.stop_text = stop_text

    def run(self):
        RoboticArmFunctions.continuousCtrlLoop(
            self.axis_curval_list, self.axis_setval_list, self.status, self.stop_text
        )
        
        
class PlayBackMotion(Thread):
    def __init__(
        self,
        axis_curval_list: "list[tk.DoubleVar]",
        status: "list[tk.BooleanVar]",
        stop_text: "list[tk.StringVar]"
    ):
        super().__init__()
        self.axis_curval_list = axis_curval_list
        self.status = status
        self.stop_text = stop_text
        
    def run(self):
        RoboticArmFunctions.playBackMotion(
            self.axis_curval_list, 1.0, self.status, self.stop_text
        )


# Write out json data to file
def writeOut(data):
    print("WRITING TO CONSOLE")
    with open(data_file, "w") as outfile:
        json.dump(data, outfile)
    outfile.close()


# Read in json data from file
def readIn():
    with open(data_file) as json_file:
        data = json.load(json_file)
    return data


# Window class definition; creates the new window for the frame
class Window(tk.Tk):

    # window constructor
    def __init__(self, width, height):
        """used to create a new instane of the window"""
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(StartPage)
        self.width = width
        self.height = height
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Used to control what happens on window close
    def on_closing(self):
        """when called allows user the chance to quit"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

    # Switch which frame is currently active in the window
    def switch_frame(self, frame_class: ttk.Frame):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        # add padding around frame then inserts in the window
        self._frame.pack(pady=20, padx=15)
        # passes Preset Height and Width
        self.wm_minsize(width=frame_class.width, height=frame_class.height)
        self.title("Robotic Arm Controller" + frame_class.window_name)
        self.eval("tk::PlaceWindow . center")


# Start Page class definition
class StartPage(ttk.Frame):
    """Start up page created using pack layout manager"""

    window_name = " - Start Up Menu"
    width, height = 500, 200

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        ttk.Label(
            self, text="Welcome to Control GUI", font=("Helvetica", 11, "bold")
        ).pack(side="top", fill="x", pady=20)
        ttk.Button(
            self, text="Settings", command=lambda: master.switch_frame(PageOne)
        ).pack(pady=10, ipady=5, ipadx=5)
        ttk.Button(
            self, text="Control / Testing", command=lambda: master.switch_frame(PageTwo)
        ).pack(pady=10, ipady=5, ipadx=5)


# Page One class definition
class PageOne(ttk.Frame):
    """PageOne creates a frame will all off the componets within it for the settings page. Uses grid layout manager."""

    window_name = " - Settings"
    width, height = 1000, 400

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        # used to read in data
        data = readIn()  # call readIn() function to read data from json file
        axis1_1_minang = data["minangs"][0]
        axis2_1_minang = data["minangs"][1]
        # Redundant information due to the fact that the second axis has 2 motors
        axis2_2_minang = data["minangs"][2]
        axis3_1_minang = data["minangs"][3]
        axis4_1_minang = data["minangs"][4]
        axis1_1_maxang = data["maxangs"][0]
        axis2_1_maxang = data["maxangs"][1]
        # Redundant information due to the fact that the second axis has 2 motors
        axis2_2_maxang = data["maxangs"][2]
        axis3_1_maxang = data["maxangs"][3]
        axis4_1_maxang = data["maxangs"][4]
        

        # create string variables that can be used to get and set the values of the entry boxes
        (
            self.axis1_1_minang_var,
            self.axis2_1_minang_var,
            self.axis2_2_minang_var,
            self.axis3_1_minang_var,
            self.axis4_1_minang_var,
        ) = (
            tk.DoubleVar(),
            tk.DoubleVar(),
            tk.DoubleVar(),
            tk.DoubleVar(),
            tk.DoubleVar(),
        )
        (
            self.axis1_1_maxang_var,
            self.axis2_1_maxang_var,
            self.axis2_2_maxang_var,
            self.axis3_1_maxang_var,
            self.axis4_1_maxang_var,
        ) = (
            tk.DoubleVar(),
            tk.DoubleVar(),
            tk.DoubleVar(),
            tk.DoubleVar(),
            tk.DoubleVar(),
        )

        # creating general labels
        address_label = ttk.Label(
            self,
            anchor="center",
            justify="center",
            text="Controller Address",
            font=("calibre", 10, "bold"),
            width=18,
        )
        minang_label = ttk.Label(
            self, text="Min Angle (°)", font=("calibre", 10, "bold")
        )
        maxang_label = ttk.Label(
            self, text="Max Angle (°)", font=("calibre", 10, "bold")
        )

        # creating a label for axis1
        axis1_label = ttk.Label(self, text="Axis 1", font=("calibre", 10, "bold"))

        # creating a values for axis1
        axis1_1_address_entry = ttk.Entry(
            self,
            justify="center",
            font=("calibre", 10, "normal"),
            state="normal",
            width=18,
        )
        self.axis1_1_minang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis1_1_minang_var,
            font=("calibre", 10, "normal"),
        )
        self.axis1_1_maxang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis1_1_maxang_var,
            font=("calibre", 10, "normal"),
        )
        # deletes and inserts the proper address in the entry boxes for them, then changes there state to readonly.
        axis1_1_address_entry.delete(0, 2)
        axis1_1_address_entry.insert(0, str(axis1_1_address))
        axis1_1_address_entry.configure(state="readonly")
        self.axis1_1_minang_var.set(axis1_1_minang)
        self.axis1_1_maxang_var.set(axis1_1_maxang)

        # creating a label for axis2
        axis2_label = ttk.Label(self, text="Axis 2", font=("calibre", 10, "bold"))

        # creating a values for axis2, which controls two seprate motors
        axis2_1_address_entry = ttk.Entry(
            self, justify="center", font=("calibre", 10, "normal"), state="normal"
        )
        self.axis2_1_minang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis2_1_minang_var,
            font=("calibre", 10, "normal"),
        )
        self.axis2_1_maxang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis2_1_maxang_var,
            font=("calibre", 10, "normal"),
        )
        axis2_2_address_entry = ttk.Entry(
            self, justify="center", font=("calibre", 10, "normal"), state="normal"
        )
        # deletes and inserts the proper address in the entry boxes for them, then changes there state to readonly.
        axis2_1_address_entry.delete(0, 2)
        axis2_1_address_entry.insert(0, str(axis2_1_address))
        axis2_1_address_entry.configure(state="readonly")
        axis2_2_address_entry.delete(0, 2)
        axis2_2_address_entry.insert(0, str(axis2_2_address))
        axis2_2_address_entry.configure(state="readonly")
        self.axis2_1_minang_var.set(axis2_1_minang)
        self.axis2_1_maxang_var.set(axis2_1_maxang)

        # creating a label for axis3
        axis3_label = ttk.Label(self, text="Axis 3", font=("calibre", 10, "bold"))

        # creating a values for axis3
        axis3_1_address_entry = ttk.Entry(
            self,
            justify="center",
            font=("calibre", 10, "normal"),
            state="normal",
            width=18,
        )
        self.axis3_1_minang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis3_1_minang_var,
            font=("calibre", 10, "normal"),
        )
        self.axis3_1_maxang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis3_1_maxang_var,
            font=("calibre", 10, "normal"),
        )
        # deletes and inserts the proper address in the entry boxes for them, then changes there state to readonly.
        axis3_1_address_entry.delete(0, 2)
        axis3_1_address_entry.insert(0, str(axis3_1_address))
        axis3_1_address_entry.configure(state="readonly")
        self.axis3_1_minang_var.set(axis3_1_minang)
        self.axis3_1_maxang_var.set(axis3_1_maxang)

        # creating a label for axis4
        axis4_label = ttk.Label(self, text="Axis 4", font=("calibre", 10, "bold"))

        # creating a values for axis4
        axis4_1_address_entry = ttk.Entry(
            self,
            justify="center",
            font=("calibre", 10, "normal"),
            state="normal",
            width=18,
        )
        self.axis4_1_minang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis4_1_minang_var,
            font=("calibre", 10, "normal"),
        )
        self.axis4_1_maxang_entry = ttk.Entry(
            self,
            justify="center",
            textvariable=self.axis4_1_maxang_var,
            font=("calibre", 10, "normal"),
        )
        # deletes and inserts the proper address in the entry boxes for them, then changes there state to readonly.
        axis4_1_address_entry.delete(0, 2)
        axis4_1_address_entry.insert(0, str(axis4_1_address))
        axis4_1_address_entry.configure(state="readonly")
        self.axis4_1_minang_var.set(axis4_1_minang)
        self.axis4_1_maxang_var.set(axis4_1_maxang)

        # create buttons
        settings = ttk.Button(
            self, text="Control / Testing", command=lambda: master.switch_frame(PageTwo)
        )
        back = ttk.Button(
            self, text="Back", command=lambda: master.switch_frame(StartPage)
        )
        save = ttk.Button(self, text="Save", command=lambda: self.updateVars())

        address_label.grid(row=0, column=1, columnspan=2, sticky="ew")
        minang_label.grid(row=0, column=3)
        maxang_label.grid(row=0, column=4)

        axis1_label.grid(row=1, column=0)
        axis1_1_address_entry.grid(row=1, column=1, columnspan=2, sticky="ew")
        self.axis1_1_minang_entry.grid(row=1, column=3)
        self.axis1_1_maxang_entry.grid(row=1, column=4, pady=10)

        axis2_label.grid(row=2, column=0)
        axis2_1_address_entry.grid(row=2, column=1)
        axis2_2_address_entry.grid(row=2, column=2)
        self.axis2_1_minang_entry.grid(row=2, column=3)
        self.axis2_1_maxang_entry.grid(row=2, column=4)

        axis3_label.grid(row=4, column=0)
        axis3_1_address_entry.grid(row=4, column=1, columnspan=2, sticky="ew")
        self.axis3_1_minang_entry.grid(
            row=4,
            column=3,
        )
        self.axis3_1_maxang_entry.grid(row=4, column=4, pady=10)

        axis4_label.grid(row=5, column=0)
        axis4_1_address_entry.grid(row=5, column=1, columnspan=2, sticky="ew")
        self.axis4_1_minang_entry.grid(row=5, column=3)
        self.axis4_1_maxang_entry.grid(row=5, column=4)

        settings.grid(row=7, column=1)
        back.grid(row=7, column=3)
        save.grid(row=7, column=4)

    # Used to update the "settings" that the user has the ability to change.
    def updateVars(self):
        print("updating called")
        axis1_1_minang = self.axis1_1_minang_var.get()
        axis1_1_maxang = self.axis1_1_maxang_var.get()
        axis2_1_minang = self.axis2_1_minang_var.get()
        axis2_1_maxang = self.axis2_1_maxang_var.get()
        axis2_2_minang = axis2_1_minang
        axis2_2_maxang = axis2_1_maxang
        axis3_1_minang = self.axis3_1_minang_var.get()
        axis3_1_maxang = self.axis3_1_maxang_var.get()
        axis4_1_minang = self.axis4_1_minang_var.get()
        axis4_1_maxang = self.axis4_1_maxang_var.get()
        minangsList = [
            axis1_1_minang,
            axis2_1_minang,
            axis2_2_minang,
            axis3_1_minang,
            axis4_1_minang,
        ]
        maxangsList = [
            axis1_1_maxang,
            axis2_1_maxang,
            axis2_2_maxang,
            axis3_1_maxang,
            axis4_1_maxang,
        ]
        data = {"minangs": minangsList, "maxangs": maxangsList}
        # passes the packed date to be written out ("saved") to the json file
        writeOut(data)


# Page Two class definition
class PageTwo(ttk.Frame):
    """PageTwo creates a frame will all of the componets within it for the control/testing page. Uses grid layout manager."""

    window_name = " - Control / Testing"
    width, height = 1000, 400

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        data = readIn()  # call readIn() function to read data from json file
        self.axis2_1_minang = data["minangs"][1]
        self.axis1_1_minang = data["minangs"][0]
        # Redundant information due to the fact that the second axis has 2 motors
        self.axis3_1_minang = data["minangs"][3]
        self.axis4_1_minang = data["minangs"][4]
        self.axis1_1_maxang = data["maxangs"][0]
        self.axis2_1_maxang = data["maxangs"][1]
        # Redundant information due to the fact that the second axis has 2 motors
        self.axis3_1_maxang = data["maxangs"][3]
        self.axis4_1_maxang = data["maxangs"][4]
        
        self.axis_minang_list = [
                                self.axis1_1_minang,
                                self.axis2_1_minang, 
                                self.axis3_1_minang, 
                                self.axis4_1_minang
                                ]
        self.axis_maxang_list = [
                                self.axis1_1_maxang,
                                self.axis2_1_maxang, 
                                self.axis3_1_maxang, 
                                self.axis4_1_maxang
                                ]

        self.control_loop_active = bool(False)
        
        # create tk.DoubleVar() that can be used to get and 
        # set the values of the entry and spinboxes
        # These tk.DoubleVar() are used to Construct a float variable. 
        # They can be changed with a .set() and .get() methods
        (
            self.axis1_1_curval_var,
            self.axis2_1_curval_var,
            self.axis3_1_curval_var,
            self.axis4_1_curval_var,
        ) = (tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar())
        (
            self.axis1_1_setval_var,
            self.axis2_1_setval_var,
            self.axis3_1_setval_var,
            self.axis4_1_setval_var,
        ) = (tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar())
        self.axis_curval_list = [
            self.axis1_1_curval_var,
            self.axis2_1_curval_var,
            self.axis3_1_curval_var,
            self.axis4_1_curval_var,
        ]
        self.axis_setval_list = [
            self.axis1_1_setval_var,
            self.axis2_1_setval_var,
            self.axis3_1_setval_var,
            self.axis4_1_setval_var,
        ]

        # creating Lables for the columns and label Frame
        self.value_frame = ttk.Frame(self)
        curval_label = ttk.Label(
            self.value_frame, text="Current Position (°)", font=("calibre", 11, "bold")
        )
        setval_label = ttk.Label(
            self.value_frame, text="Set Position (°)", font=("calibre", 11, "bold")
        )

        # creating a label for axis1
        axis1_label = ttk.Label(
            self.value_frame, text="Axis 1 (Base)", font=("calibre", 11, "bold")
        )
        # creating a values for axis1
        axis1_1_curval_entry = ttk.Entry(
            self.value_frame,
            textvariable=self.axis1_1_curval_var,
            font=("calibre", 11, "normal"),
            state="readonly",
        )
        axis1_1_setval_entry = ttk.Spinbox(
            self.value_frame,
            from_=self.axis1_1_minang,
            to=self.axis1_1_maxang,
            increment=1.0,
            textvariable=self.axis1_1_setval_var,
            font=("calibre", 11, "normal"),
            format = "%.1f",
        )
        self.axis1_1_curval_var.set(0.0)
        self.axis1_1_setval_var.set(0.0)

        # creating a label for axis2
        axis2_label = ttk.Label(
            self.value_frame, text="Axis 2 (Shoulder)", font=("calibre", 11, "bold")
        )
        # creating a values for axis2
        axis2_1_curval_entry = ttk.Entry(
            self.value_frame,
            textvariable=self.axis2_1_curval_var,
            font=("calibre", 11, "normal"),
            state="readonly",
        )
        axis2_1_setval_entry = ttk.Spinbox(
            self.value_frame,
            from_=self.axis2_1_minang,
            to=self.axis2_1_maxang,
            increment=1.0,
            textvariable=self.axis2_1_setval_var,
            font=("calibre", 11, "normal"),
            format = "%.1f",
        )
        self.axis2_1_curval_var.set(0.0)
        self.axis2_1_setval_var.set(0.0)

        # creating a label for axis3
        axis3_label = ttk.Label(
            self.value_frame, text="Axis 3 (Elbow)", font=("calibre", 11, "bold")
        )
        # creating a values for axis3
        axis3_1_curval_entry = ttk.Entry(
            self.value_frame,
            textvariable=self.axis3_1_curval_var,
            font=("calibre", 11, "normal"),
            state="readonly",
        )
        axis3_1_setval_entry = ttk.Spinbox(
            self.value_frame,
            from_=self.axis3_1_minang,
            to=self.axis3_1_maxang,
            increment=1.0,
            textvariable=self.axis3_1_setval_var,
            font=("calibre", 11, "normal"),
            format = "%.1f"
        )
        self.axis3_1_curval_var.set(0.0)
        self.axis3_1_setval_var.set(0.0)

        # creating a label for axis4
        axis4_label = ttk.Label(
            self.value_frame,
            text="Axis 4 (Wrist Rotation)",
            font=("calibre", 11, "bold"),
        )
        # creating a values for axis4
        axis4_1_curval_entry = ttk.Entry(
            self.value_frame,
            textvariable=self.axis4_1_curval_var,
            font=("calibre", 11, "normal"),
            state="readonly",
        )
        axis4_1_setval_entry = ttk.Spinbox(
            self.value_frame,
            from_=self.axis4_1_minang,
            to=self.axis4_1_maxang,
            increment=1.0,
            textvariable=self.axis4_1_setval_var,
            font=("calibre", 11, "normal"),
            format = "%.1f"
        )
        self.axis4_1_curval_var.set(0.0)
        self.axis4_1_setval_var.set(0.0)

        # Putting the labels and entry boxes into the value_frame
        curval_label.grid(row=0, column=1)
        setval_label.grid(row=0, column=2)
        axis1_label.grid(row=1, column=0)
        axis1_1_curval_entry.grid(row=1, column=1)
        axis1_1_setval_entry.grid(row=1, column=2)
        axis2_label.grid(row=2, column=0)
        axis2_1_curval_entry.grid(row=2, column=1)
        axis2_1_setval_entry.grid(row=2, column=2)
        axis3_label.grid(row=3, column=0)
        axis3_1_curval_entry.grid(row=3, column=1)
        axis3_1_setval_entry.grid(row=3, column=2)
        axis4_label.grid(row=4, column=0)
        axis4_1_curval_entry.grid(row=4, column=1)
        axis4_1_setval_entry.grid(row=4, column=2)

        # create buttons
        navigation_frame = ttk.Labelframe(self, labelanchor="n")
        navigation_label = ttk.Label(
            navigation_frame, text="Page Navigation", font=("calibre", 11, "bold")
        )
        navigation_frame.configure(labelwidget=navigation_label)
        settings = ttk.Button(
            navigation_frame,
            text="Settings",
            command=lambda: master.switch_frame(PageOne),
        )
        back = ttk.Button(
            navigation_frame,
            text="Back",
            command=lambda: master.switch_frame(StartPage),
        )
        settings.pack(side="left")
        back.pack(side="left")

        # Create Controls Frame and Place Components inside
        self.gripper_state_text = tk.StringVar()
        self.controls_frame = ttk.Labelframe(self, labelanchor="n")
        controls_label = ttk.Label(
            self.controls_frame, text="Robot Controls", font=("calibre", 11, "bold")
        )
        self.controls_frame.configure(labelwidget=controls_label)
        self.move_arm = ttk.Button(
            self.controls_frame,
            text="Move Arm to Set Values",
            command=lambda: self.moveArm(),
        )
        move_arm_label = ttk.Label(
            self.controls_frame, text="Arm Control: ", font=("calibre", 11, "bold")
        )
        gripper_label = ttk.Label(
            self.controls_frame, text="Gripper Control: ", font=("calibre", 11, "bold")
        )
        self.gripper_control = ttk.Button(
            self.controls_frame,
            textvariable=self.gripper_state_text,
            command=lambda: self.gripperControl(),
        )
        self.gripper_state_text.set("Close")
        zero_axis_label = ttk.Label(
            self.controls_frame, text="Zero Axis: ", font=("calibre", 11, "bold")
        )

        # create buttons to zero axis position and place them in a frame whose master is controls_frame
        zero_axis_controls = ttk.Frame(self.controls_frame)
        self.axis1_zero = ttk.Button(
            zero_axis_controls,
            text="Zero Axis 1",
            command=lambda: self.zeroAxisPosition(1, self.axis1_zero),
        )
        self.axis2_zero = ttk.Button(
            zero_axis_controls,
            text="Zero Axis 2",
            command=lambda: self.zeroAxisPosition(2, self.axis2_zero),
        )
        self.axis3_zero = ttk.Button(
            zero_axis_controls,
            text="Zero Axis 3",
            command=lambda: self.zeroAxisPosition(3, self.axis3_zero),
        )
        self.axis4_zero = ttk.Button(
            zero_axis_controls,
            text="Zero Axis 4",
            command=lambda: self.zeroAxisPosition(4, self.axis4_zero),
        )
        self.all_axis_zero = ttk.Button(
            zero_axis_controls,
            text="Zero ALL",
            command=lambda: {
                self.zeroAxisPosition(1, self.all_axis_zero),
                self.zeroAxisPosition(2, self.all_axis_zero),
                self.zeroAxisPosition(3, self.all_axis_zero),
                self.zeroAxisPosition(4, self.all_axis_zero),
            },
        )
        self.axis1_zero.pack(side="left", expand=True, fill="x")
        self.axis2_zero.pack(side="left", expand=True, fill="x")
        self.axis3_zero.pack(side="left", expand=True, fill="x")
        self.axis4_zero.pack(side="left", expand=True, fill="x")
        self.all_axis_zero.pack(side="left", expand=True, fill="x")

        gripper_label.grid(row=1, column=0)
        move_arm_label.grid(row=2, column=0)
        self.gripper_control.grid(row=1, column=1, pady=5)
        self.move_arm.grid(row=2, column=1)
        zero_axis_label.grid(row=3, column=0)
        zero_axis_controls.grid(row=3, column=1, columnspan=5, pady=5)

        # create adjustment buttons and pack them in a frame
        self.adj_val_buttons_frame = ttk.Labelframe(self, labelanchor="n")
        adj_val_label = ttk.Label(
            self.adj_val_buttons_frame,
            text="Adjust Position (°)",
            font=("calibre", 11, "bold"),
        )
        self.adj_val_buttons_frame.configure(labelwidget=adj_val_label)
        for i in range(1, 5):
            axis_1_0_setval_add = ttk.Button(
                self.adj_val_buttons_frame,
                text="+1.0",
                command=lambda i=i: self.changeSetVal(i, 1.0),
            )
            axis_1_0_setval_sub = ttk.Button(
                self.adj_val_buttons_frame,
                text="-1.0",
                command=lambda i=i: self.changeSetVal(i, -1.0),
            )
            axis_5_0_setval_add = ttk.Button(
                self.adj_val_buttons_frame,
                text="+5.0",
                command=lambda i=i: self.changeSetVal(i, 5.0),
            )
            axis_5_0_setval_sub = ttk.Button(
                self.adj_val_buttons_frame,
                text="-5.0",
                command=lambda i=i: self.changeSetVal(i, -5.0),
            )
            axis_10_0_setval_add = ttk.Button(
                self.adj_val_buttons_frame,
                text="+10.0",
                command=lambda i=i: self.changeSetVal(i, 10.0),
            )
            axis_10_0_setval_sub = ttk.Button(
                self.adj_val_buttons_frame,
                text="-10.0",
                command=lambda i=i: self.changeSetVal(i, -10.0),
            )
            axis_1_0_setval_add.grid(row=i, column=1)
            axis_1_0_setval_sub.grid(row=i, column=6)
            axis_5_0_setval_add.grid(row=i, column=2)
            axis_5_0_setval_sub.grid(row=i, column=5)
            axis_10_0_setval_add.grid(row=i, column=3)
            axis_10_0_setval_sub.grid(row=i, column=4)

        # Create Frame For Options and Place Componets within
        options_frame = ttk.Labelframe(self, labelanchor="n")
        options_label = ttk.Label(
            options_frame, text="Options", font=("calibre", 11, "bold")
        )
        options_frame.configure(labelwidget=options_label)
        self.live_control_state = tk.BooleanVar()
        self.record_state = tk.BooleanVar()
        self.play_back_state = tk.BooleanVar()
        self.live_control_cb = ttk.Checkbutton(
            options_frame,
            variable=self.live_control_state,
            onvalue=True,
            offvalue=False,
            command=lambda: self.confirmLiveAxisControl(),
        )
        live_control_label = ttk.Label(
            options_frame, text="Enable Live Control: ", font=("calibre", 11, "bold")
        )
        self.record_cb = ttk.Checkbutton(
            options_frame, variable=self.record_state, onvalue=True, offvalue=False, state='disable'
        )
        record_state_label = ttk.Label(
            options_frame, text="Record Movements: ", font=("calibre", 11, "bold")
        )
        self.play_back_cb = ttk.Checkbutton(
            options_frame,
            variable=self.play_back_state,
            onvalue=True,
            offvalue=False,
            command=lambda: self.playBackEnable(),
        )
        play_back_label = ttk.Label(
            options_frame, text="Playback Movements: ", font=("calibre", 11, "bold")
        )
        live_control_label.grid(row=0, column=0)
        self.live_control_cb.grid(row=0, column=1)
        record_state_label.grid(row=1, column=0)
        self.record_cb.grid(row=1, column=1)
        play_back_label.grid(row=2, column=0)
        self.play_back_cb.grid(row=2, column=1)

        # Create Program Controls frame (will include Run/Pause, Stop)
        program_controls_frame = ttk.Labelframe(self, labelanchor="n")
        program_controls_label = ttk.Label(
            program_controls_frame,
            text="Program Controls",
            font=("calibre", 11, "bold"),
        )
        program_controls_frame.configure(labelwidget=program_controls_label)
        self.run_pause_button_state = tk.BooleanVar()
        self.stop_button_state = tk.BooleanVar()
        self.run_pause_button_text = tk.StringVar(value="Run")
        self.stop_button_text = tk.StringVar(value="E-Stop")
        self.run_pause_button = ttk.Button(
            program_controls_frame,
            textvariable=self.run_pause_button_text,
            command=lambda: self.runPauseUpdate(),
            state='disable'
        )
        self.stop_button = ttk.Button(
            program_controls_frame,
            textvariable=self.stop_button_text,
            command=lambda: self.stopUpdate(),
        )
        self.run_pause_button.pack(side="top")
        self.stop_button.pack(side="top")

        # placing sub frames into main frame
        self.value_frame.grid(row=0, column=0)
        self.adj_val_buttons_frame.grid(row=0, column=1, columnspan=2)
        navigation_frame.grid(row=2, column=0, columnspan=3)
        self.controls_frame.grid(row=1, column=0)
        options_frame.grid(row=1, column=1)
        program_controls_frame.grid(row=1, column=2)

        # Used to pass the status of the live control bit to allow the termination of the Contiunos Control Loop
        self.gripper_state = tk.BooleanVar()
        self.status = [
            self.live_control_state,
            self.record_state,
            self.gripper_state,
            self.play_back_state,
            self.run_pause_button_state,
            self.stop_button_state,
        ]
        '''[self.live_control_state, self.record_state, self.gripper_state, 
        self.play_back_state, self.start_pause_button_state, self.stop_button_state]'''
        
        self.program_controls_text = [self.stop_button_text, self.run_pause_button_text]
        
        start_up_thread = PageTwoStartUp(self.axis_curval_list, self.axis_setval_list)
        start_up_thread.setDaemon(True)
        start_up_thread.start()

    def runPauseUpdate(self):
        if self.run_pause_button_text.get() == "Run":
            self.run_pause_button_state.set(True)
            self.run_pause_button_text.set("Pause")
        else:
            self.run_pause_button_state.set(False)
            self.run_pause_button_text.set("Run")

    def stopUpdate(self):
        if self.stop_button_text.get() == "E-Stop":
            self.stop_button_state.set(True)
            self.stop_button_text.set("Reset E-Stop")
            messagebox.showinfo(
                "Attention!",
                "E-Stop pressed on GUI, All motion stopped. "
                + "Please attempt to reset position of arm "
                + "by manually moving axis slowly while powered down "
                + "and resetting the pi and controllers. "
                + "OR Another option is to reset the e-stop to regain control "
                + "and use a combination of moving the axis using by setting the "
                + "position and pressing the move arm button. ",
            )
        elif self.stop_button_text.get() == "Reset E-Stop":
            if messagebox.askyesno(
                "Attention!",
                "Resetting E-Stop? Must return arm back to safe state to ensure no damage. Continue?",
            ):
                self.stop_button_state.set(False)
                self.stop_button_text.set("E-Stop")

    def gripperControl(self):
        self.gripper_control.configure(state="disable")
        gripper_thread = GripperControl(self.gripper_state_text.get())
        gripper_thread.setDaemon(True)
        gripper_thread.start()
        if self.gripper_state_text.get() == "Open":
            self.gripper_state_text.set("Opening")
        elif self.gripper_state_text.get() == "Close":
            self.gripper_state_text.set("Closing")
        # used to monitor the state of the gripper control thread
        self.monitorGripperControl(gripper_thread)

    def monitorGripperControl(self, thread=Thread):
        """Used to monitor the state of the control thread for the gripper.
        Also used to update the state of the button after the thread is done

        Args:
            thread: only pass the GripperControl() thread to this function.
        """
        if thread.is_alive():
            self.after(100, lambda: self.monitorGripperControl(thread))
        else:
            if self.gripper_state_text.get() == "Closing":
                self.gripper_state_text.set("Open")
                self.gripper_state.set(False)
            if self.gripper_state_text.get() == "Opening":
                self.gripper_state_text.set("Close")
                self.gripper_state.set(True)
            self.gripper_control.configure(state="normal")

    def moveArm(self):
        self.move_arm.configure(state="disable")
        self.control_loop_thread = AsyncControl(
            self.axis_curval_list, self.axis_setval_list, self.status, self.program_controls_text
        )
        self.control_loop_thread.setDaemon(True)
        self.control_loop_thread.start()
        self.control_loop_active = True

        self.monitorMoveArm(self.control_loop_thread)

    def monitorMoveArm(self, thread=Thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitorMoveArm(thread))
        else:
            self.move_arm.configure(state="normal")
            self.control_loop_active = False

    def zeroAxisPosition(self, axisNum, button=ttk.Button):
        self.ttk_button = button
        self.ttk_button.configure(state="disable")
        zero_axis_thread = ZeroAxisPosition(
            axisNum, self.axis_curval_list, self.axis_setval_list
        )
        zero_axis_thread.setDaemon(True)
        zero_axis_thread.start()

        self.monitorZeroAxisPosition(zero_axis_thread)

    def monitorZeroAxisPosition(self, thread=Thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitorZeroAxisPosition(thread))
        else:
            self.ttk_button.configure(state="normal")
            
    # TODO: Write method for validating input and implement to keep value errors. unable to get working. 
    # def validateInput(self, spinbox_name: 'str', user_input):
    #     spinbox: "ttk.Spinbox"
    #     spinbox = self.nametowidget(spinbox_name)
    #     minval = float(spinbox.config('from'))
    #     maxval = float(spinbox.config('to'))
    #     try:
    #         user_input = float(user_input)
    #     except:
    #         return False 
    #     if user_input not in range(minval, maxval):
    #         print ("Out of range")
    #         return False
    #     else:
    #         return True
        

    # change set value definition
    def changeSetVal(self, axis_num, change_val):
        """Used to as the command to be executed when the adjustment buttons are used to change the position set value"""
        if 0 < axis_num < 5:
            num = self.axis_setval_list[axis_num-1].get()
            new_num = num + change_val
            if new_num < self.axis_minang_list[axis_num-1]:
                new_num = self.axis_minang_list[axis_num-1]
            if new_num > self.axis_maxang_list[axis_num-1]:
                new_num = self.axis_maxang_list[axis_num-1]
            self.axis_setval_list[axis_num-1].set(new_num)
        else:
            print("Error: axis does not exist!")

    def confirmLiveAxisControl(self):
        if self.live_control_state.get() == True and self.control_loop_active != True:
            if messagebox.askokcancel(
                "Attention!!",
                "CAUTION: Enabling live control of the individual axis!\nUse caution! Do you want to continue?",
            ):
                self.run_pause_button.configure(state = "enable")
                self.move_arm.configure(state="disable")
                self.play_back_cb.configure(state="disable")
                self.record_cb.configure(state = "enable")
                self.readonlyChildren(self.value_frame)
                self.live_axis_control_thread = LiveAxisControl(
                    self.axis_curval_list, self.axis_setval_list, self.status, self.program_controls_text
                )
                self.live_axis_control_thread.setDaemon(True)
                self.live_axis_control_thread.start()
                self.monitorLiveAxisControl(self.live_axis_control_thread)
                return
            else:
                self.live_control_state.set(False)
        else:
            self.move_arm.configure(state="normal")
            self.live_control_state.set(False)

    def monitorLiveAxisControl(self, thread=Thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitorLiveAxisControl(thread))
        else:
            self.move_arm.configure(state="normal")
            self.play_back_cb.configure(state="normal")
            self.run_pause_button_text.set("Run")
            self.run_pause_button_state.set(False)
            self.run_pause_button.configure(state = "disable")
            self.live_control_state.set(False)
            self.record_cb.configure(state = "disable")
            self.record_state.set(False)
            self.enableChildren(self.value_frame)

    def playBackEnable(self):
        if self.play_back_state.get() and self.control_loop_active != True:
            if messagebox.askokcancel(
                "Attention!!", "Enabling Motion Play Back\nDo you want to continue?"
            ):
                self.run_pause_button.configure(state = "enable")
                self.record_cb.configure(state = "disable")
                self.live_control_cb.configure(state = 'disable')
                # Disable all spinboxs on value_frame
                self.disableChildren(self.value_frame)
                # Disable all buttons on the controls_frame
                self.disableChildren(self.controls_frame)
                # Disable all buttons on the adj_val_buttons_frame
                self.disableChildren(self.adj_val_buttons_frame)
                # create new thread  instance to handel motion playback
                self.play_back_motion_thread = PlayBackMotion(self.axis_curval_list,self.status, self.program_controls_text)
                self.play_back_motion_thread.setDaemon(True) # use to make it so the thread will shut down after window is closed or main thread is exited
                self.play_back_motion_thread.start() # Start theard 
                self.monitorPlayBackMotion(self.play_back_motion_thread) # called to monitor thread and reset states of buttons when it is done. 
            else:
                self.play_back_state.set(False) # uncheck the clicked check box
        else:
            self.play_back_state.set(False) # uncheck the clicked check box

            
    def monitorPlayBackMotion(self, thread=Thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitorPlayBackMotion(thread))
        else:
            # Enable all spinboxs on value_frame
            self.enableChildren(self.value_frame)
            # Enable all buttons on the controls_frame
            self.enableChildren(self.controls_frame)
            # Enable all buttons on the adj_val_buttons_frame
            self.enableChildren(self.adj_val_buttons_frame)
            # Make sure play_back_enable is set to false
            self.play_back_state.set(False)
            self.run_pause_button_text.set("Run")
            self.run_pause_button_state.set(False)
            self.run_pause_button.configure(state = "disable")
            self.record_cb.configure(state = "enable")
            self.live_control_cb.configure(state = 'enable')
        

    def disableChildren(self, frame: Union[ttk.LabelFrame, ttk.Frame]):
        """Used to disable the children inputs on the screen. Will not gray out labels.

        Args:
            frame (Union[ttk.LabelFrame , ttk.Frame]): must be a ttk.Frame or ttk.LabelFrame
        """
        for child in frame.winfo_children():
            if child.widgetName == "ttk::button" or child.widgetName == "ttk::spinbox":
                child.configure(state="disable")
            if (
                child.widgetName == "ttk::lableframe"
                or child.widgetName == "ttk::frame"
            ):
                self.disableChildren(child)
                

    def enableChildren(self, frame: Union[ttk.LabelFrame, ttk.Frame]):
        """Used to disable the children inputs on the screen. Will reenable all children buttons and spinbox

        Args:
            frame (Union[ttk.LabelFrame , ttk.Frame]): _description_
        """
        for child in frame.winfo_children():
            if child.widgetName == "ttk::button" or child.widgetName == "ttk::spinbox":
                child.configure(state="normal")
            if (
                child.widgetName == "ttk::lableframe"
                or child.widgetName == "ttk::frame"
            ):
                self.enableChildren(child)
                
    def readonlyChildren(self, frame: Union[ttk.LabelFrame, ttk.Frame]):
        """Used to disable the children inputs on the screen. Will not gray out labels.

        Args:
            frame (Union[ttk.LabelFrame , ttk.Frame]): must be a ttk.Frame or ttk.LabelFrame
        """
        for child in frame.winfo_children():
            if child.widgetName == "ttk::spinbox":
                child.configure(state="readonly")
            if (
                child.widgetName == "ttk::lableframe"
                or child.widgetName == "ttk::frame"
            ):
                self.readonlyChildren(child)
                



