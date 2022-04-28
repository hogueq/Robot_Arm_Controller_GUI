#
# File: RoboticArmFunctions.py
# Date: 04/19/2022
# Author: Quinn Hogue
# Contact Info: quinnhogue24@gmail.com
# Purpose: Functions and Control Logic For Robotic Arm
#

# imports
from asyncore import loop
import json
import time
from turtle import position
from typing import List
import StepperControllerFunctions
from StepperControllerFunctions import TicI2C
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from tkinter import BooleanVar, DoubleVar, StringVar, messagebox
from tkinter import filedialog as fd

# Declare Variables
axis1_1_address, axis2_1_address, axis2_2_address, axis3_1_address, axis4_1_address = (
    14,
    15,
    16,
    17,
    18,
)

# create an instance of the TicI2C for each of the axis motor controllers
tic_axis1_1 = TicI2C(StepperControllerFunctions.bus, axis1_1_address)
tic_axis2_1 = TicI2C(StepperControllerFunctions.bus, axis2_1_address)
tic_axis2_2 = TicI2C(StepperControllerFunctions.bus, axis2_2_address)
tic_axis3_1 = TicI2C(StepperControllerFunctions.bus, axis3_1_address)
tic_axis4_1 = TicI2C(StepperControllerFunctions.bus, axis4_1_address)

# Set up the Servo Used for the Gripper
factory = PiGPIOFactory(host="localhost")
gripper = Servo(
    12,
    pin_factory=factory,
    min_pulse_width=0.45 / 1000,
    max_pulse_width=(0.5 + 0.6) / 1000,
    frame_width=20 / 1000,
)
"""min_pulse_width sets the close postion, max_pulse_width sets the open position - For Gripper Servo"""

controllers = [tic_axis1_1, tic_axis2_1, tic_axis2_2, tic_axis3_1, tic_axis4_1]
"""Axis1,Axis2_1,Axis2_2,Axis3,Axis4"""

# section not complete
# TODO: Will not be implemented by Team 7 Class of 2022, but may be used by future students
def homeArm():
    """Will be used for the section of code the preforms the homing of the robotic arm."""
    pass


staticmethod
def continousCtrlLoop(
    current_positions: "list[DoubleVar]",
    new_positions: "list[DoubleVar]",
    status: "list[BooleanVar]",
    stop_text: "list[BooleanVar]",
    out_file=None,
):
    """Used for the continous control of the axis.

    Args:
        current_positions (list[StringVars]): Contains the Current Positions In Mutable Form
        new_positions (list[StringVars]): Contains the Set Positions In Mutable Form
        status (list[BooleanVars]): Contains the Status In Mutable Form
    """
    global controllers
    kill_switch = False
    status[5].set(False)
    temp_position = [0.0, 0.0, 0.0, 0.0]
    temp_gripper_state = status[2].get()
    data = list() # will be used to append dictionarys containing values to create the final json file
    # While the check box for Live Motion Is Checked
    while status[0].get(): 
        if not status[4].get(): # Waits for the RUN button to be pressed, if it gets pressed again it will pause the live actions
            continue
        # if the record checkbox is checked and there is no outfile open: Prompt User for a file to save as.
        if status[1].get() and out_file == None: 
            out_file = fd.asksaveasfile(
                title="Select a File to Be Written or Enter New File Name",
                confirmoverwrite=True,
                defaultextension="*.json",
                initialdir="/home/pi/Desktop/RecordedPaths",
                filetypes=[("Json file", "*.json")],
                initialfile="*.json",
            )
            # check to see if an outfile was given if not it means the user pressed cancel. Set the record check box back to zero. 
            if out_file == None: 
                messagebox.showwarning('Attention!',"Error: File did not open or not given. Not recording!")
                status[1].set(False) # reset check box for record back to false. 
        # loop for incrementing through the 4 different axis inputs. counts from 1 - 4
        for i in range(1, 5):
            # if run is not enabled break out of loop inorder to get back to idle pause loop. 
            if not status[4].get():
                break
            # if new position does not equal current position or current state of gripper does not match the temp state: 
            if ( new_positions[i - 1].get() != current_positions[i - 1].get()
                or status[2].get() != temp_gripper_state
            ): 
                # Only send new axis position if it changes
                if (new_positions[i - 1].get() != current_positions[i - 1].get()):  
                    axisControl(i, new_positions)
                # if new position does not equal temp_position and status[1].get() returns true and out_file not closed
                if (new_positions[i - 1].get() != temp_position[i - 1] 
                    or status[2].get() != temp_gripper_state):  
                    data.append(
                        {
                        "AxisNum": i,
                        "Position": new_positions[i - 1].get(),
                        "Gripper State": status[2].get(),
                        }
                    )
                    # sets temp_poition to the new position that was just sent to the controllers
                    temp_position[i - 1] = new_positions[i - 1].get()  
                # sets temp grip to new position 
                temp_gripper_state = status[2].get()
            updateCurVal(current_positions)
            
            try:
                if controllers[i].get_kill_switch_status() == True or status[5].get():
                    kill_switch = True
                    if  not status[5].get():
                        status[5].set(True)
                        stop_text[0].set("Reset E-Stop")
                    else:      
                        controllers[0].enter_safe_start()
                        controllers[1].enter_safe_start()
                        controllers[2].enter_safe_start()
                        controllers[3].enter_safe_start()
                        controllers[4].enter_safe_start()
                    break
            except:
                msg = str(
                    "Error: Not responding. Could not get_kill_switch_status(), please check controller.\nThen restart Live Axis Control"
                )
                messagebox.showwarning(title="Attention!!", message=msg)
                if not status[1].get() and out_file != None and not out_file.closed:
                    json.dump(data, out_file)
                    out_file.close()
                return
            # time.sleep(0.5)
            if not status[1].get() and out_file != None and not out_file.closed:
                json.dump(data, out_file)
                out_file.close()

        if kill_switch:
            break
        

    if kill_switch:
        if messagebox.askretrycancel(
            title="Attention!!", message="Kill Switch Pressed, Motion Stopped"
        ):  
            stop_text[0].set("E-Stop")
            continousCtrlLoop(current_positions, new_positions, status, stop_text, out_file)
            if out_file != None and not out_file.closed:
                json.dump(data, out_file)
                out_file.close()
            return
        else:
            messagebox.showinfo(
                "Attention!",
                "E-Stop pressed on GUI, All moition stopped. "
                + "Please attempt to reset position of arm "
                + "by manually moving axis slowly while powered down "
                + "and resetting the pi and controllers. "
                + "OR Another opition is to reset the e-stop to regain control "
                + "and use a combination of moving the axis using by setting the "
                + "position and pressing the move arm button. ",
            )
    if out_file != None and not out_file.closed:
        json.dump(data, out_file)
        out_file.close()
    return



staticmethod
def ctrlLoop(
    current_positions: "list[DoubleVar]",
    new_positions: "list[DoubleVar]",
    status: "list[BooleanVar]",
    stop_text: "list[StringVar]"):
    """Used to send commands to each indivual axis

    Args:
        current_positions (list[StringVars]): Contains the Current Positions In Mutable Form
        new_positions (list[StringVars]): Contains the Set Positions In Mutable Form
        status (list[BooleanVars]): Contains the Status In Mutable Form

    """
    # print('axis control start')
    global controllers
    kill_switch = False
    status[5].set(False)
    # go axis by axis to send commands
    for i in range(1,5):
        if not new_positions[i-1].get() == current_positions[i-1].get():
            axisControl(i, new_positions)
            t1 = time.time()
            while True:
                t2 = time.time()
                execution_time = t2 - t1
                updateCurVal(current_positions)
                keepActiveWhileMoving(i)
                try:
                    if controllers[i].get_kill_switch_status() == True or status[5].get():
                        kill_switch = True
                        if  not status[5].get():
                            status[5].set(True)
                            stop_text[0].set("Reset E-Stop")
                        else:   
                            controllers[0].halt_and_hold()
                            controllers[1].halt_and_hold()
                            controllers[2].halt_and_hold()
                            controllers[3].halt_and_hold()
                            controllers[4].halt_and_hold()
                            
                            controllers[0].enter_safe_start()
                            controllers[1].enter_safe_start()
                            controllers[2].enter_safe_start()
                            controllers[3].enter_safe_start()
                            controllers[4].enter_safe_start()
                        break
                except:
                    msg = str(
                        "Error: Controller responding. Could not get_kill_switch_status(), please check controller.\nThen attemp to press move arm again"
                    )
                    messagebox.showwarning(title="Attention!!", message=msg)
                    return
                if new_positions[i-1].get() == current_positions[i-1].get():
                    break
                elif execution_time > 15.0:
                    break
            time.sleep(1)
            if kill_switch:
                break

        # check to see if killswitch was pressed
        if kill_switch:
            if messagebox.askretrycancel(
                title="Attention", message="Kill Switch Pressed, Motion Stopped! GUI Reset must be pressed"
            ):
                stop_text[0].set("E-Stop")
                ctrlLoop(current_positions, new_positions, status, stop_text)
                return
            else:
                messagebox.showinfo(
                    "Attention!",
                    "E-Stop pressed on GUI, All moition stopped. "
                    + "Please attempt to reset position of arm "
                    + "by manually moving axis slowly while powered down "
                    + "and resetting the pi and controllers. "
                    + "OR Another opition is to reset the e-stop to regain control "
                    + "and use a combination of moving the axis using by setting the "
                    + "position and pressing the move arm button. ",
                )
                return


staticmethod
def updateCurVal(cur_val_vars: "list[DoubleVar]"):
    """Used to pull the current posistion values frome the stepper controllers
    it has to multiple the value by 0.018 degrees to get the value the will be displayed

    Args:
        cur_val_vars: list[DoubleVar] : a list of DoubleVars passed from the GUI used to update the value matching text boxes
    """

    try:
        cur_val_vars[0].set(
            round(tic_axis1_1.get_current_position() * 0.018,1)
        )  # 0.018 degrees/step
    except:
        print("Error: axis 1 not responding, check controller!")
    try:
        cur_val_vars[1].set(
            round(tic_axis2_1.get_current_position() * 0.018, 1) 
        )  # 0.018 degrees/step
    except:
        print("Error: axis 2 not responding, check controller!")
    try:
        cur_val_vars[2].set(
            round(tic_axis3_1.get_current_position() * 0.018, 1)
        )  # 0.018 degrees/step
    except:
        print("Error: axis 3 not responding, check controller!")
    try:
        cur_val_vars[3].set(
            round(tic_axis4_1.get_current_position() * 0.05625, 1)
        )  # 0.05625 degrees/step (controller set for 1/32step mode)
    except:
        print("Error: axis 4 not responding, check controller!")


staticmethod
def axisControl(axisNum, newPosition):
    """Used to set new target positions for each axis

    Args:
        axisNum (integer): used to select the desired axis
        newPosition (List[stringvars]): used to pass the new position text from the GUI to the controller
    """
    global controllers
    target_1 = int(newPosition[axisNum - 1].get() / 0.018)
    if axisNum == 1:
        try:
            controllers[axisNum - 1].set_target_position(target_1)
            controllers[axisNum - 1].exit_safe_start()
        except:
            print("Error: axis", axisNum, " not responding, please check controller")
        # print("axis", axisNum, " target:", target_1)
    elif axisNum == 2:
        target_2 = -target_1
        try:
            controllers[axisNum].set_target_position(target_2)
            controllers[axisNum - 1].set_target_position(target_1)
            controllers[axisNum].exit_safe_start()
            controllers[axisNum - 1].exit_safe_start()
        except:
            print("Error: axis", axisNum, " not responding, please check controller")
        # print("axis", axisNum, " target:", target_2)
    else:
        if (
            axisNum == 4
        ):  # used to fixed the number before it is sent to the controller for the forth axis
            target_1 = int(target_1 / 3.125)
        # print("axis", axisNum, " target:", target_1)
        try:
            controllers[axisNum].set_target_position(target_1)
            controllers[axisNum].exit_safe_start()
        except:
            print("Error: axis", axisNum, " not responding, please check controller")


staticmethod
def gripActivate():
    """Function closes the gripper"""
    gripper.min()
    time.sleep(1.0)


staticmethod
def gripDeactivate():
    """Function opens the grippers"""
    gripper.max()
    time.sleep(1.0)


staticmethod
def set_current_position(axis_num, current_position, axis_setval_list, axis_curval_list):
    """Used to set new current position (Zero the position of the specified axis)
    Args:
        axisNum (interger): used to select the desired axis
        currentPosition (interger): used to pass the new current position from the GUI to the controller
    """
    global controllers
    target_1 = int(current_position / 0.018)
    if axis_num == 1:
        try:
            controllers[axis_num - 1].set_current_position(target_1)
        except:
            print("Error: axis", axis_num, " not responding, please check controller")
            return
        axis_setval_list[axis_num - 1].set("0.0")
        print("axis", axis_num, " target1:", target_1)
    elif axis_num == 2:
        target_2 = -target_1
        try:
            controllers[axis_num].set_current_position(target_2)
            controllers[axis_num - 1].set_current_position(target_1)
        except:
            print("Error: axis", axis_num, " not responding, please check controller")
            return
        axis_setval_list[axis_num - 1].set("0.0")
        print("axis", axis_num, " target2:", target_2)
    else:
        try:
            if (
                axis_num == 4
            ):  # used to fixed the number before it is sent to the controller for the forth axis
                target_1 = int(target_1 / 3.125)
            controllers[axis_num].set_current_position(target_1)
        except:
            print("Error: axis", axis_num, " not responding, please check controller")
            return
        axis_setval_list[axis_num - 1].set("0.0")
        print("axis", axis_num, " target1:", target_1)
    updateCurVal(
        axis_curval_list
    )  # call the function to update the current values on the display


staticmethod
def playBackMotion(
    current_positions: "list[DoubleVar]",
    step_speed, 
    status: "list[BooleanVar]", 
    stop_text: "list[BooleanVar]"
):
    """_summary_

    Args:
        current_positions (list[DoubleVar]): _description_
        step_speed (_type_): _description_
        status (list[BooleanVar]): _description_
        stop_text (list[BooleanVar]): _description_
    """
    commands: "list[dict]" #declare the type hint for the commands varible 
    position = [
        DoubleVar(),
        DoubleVar(),
        DoubleVar(),
        DoubleVar(),
    ]
    temp_gripper_state = status[2].get()
    # ask user to select a file to be played back.
    in_file = fd.askopenfile(
        title="Select file to be played back",
        mode="r",
        defaultextension="*.json",
        initialdir="/home/pi/Desktop/RecordedPaths",
        filetypes=[("Json file", "*.json")],
    )
    try:
        commands = json.load(in_file)
    except:
        # print error message to console if json can't be loaded
        print("Error: could not load json file")
        return
    in_file.close  # after file load it can be closed
    findImportantControlPoints(
        commands
    )  # used to find the local min and local max, when axis num changes, or when gripper state changes.
    for i in range(0, len(commands)):
        while not status[4].get():
            continue
        axis_num = commands[i]["AxisNum"]
        position[axis_num - 1].set(commands[i]["Position"])
        gripper_state = commands[i]["Gripper State"]
        if gripper_state != temp_gripper_state:
            if gripper_state:
                gripActivate()
            if not gripper_state:
                gripDeactivate()
        temp_gripper_state = status[2].get()
        axisControl(axis_num, position)
        while current_positions[axis_num - 1].get() != position[axis_num - 1].get():
            updateCurVal(current_positions)
            keepActiveWhileMoving(axis_num)
            if (controllers[axis_num - 1].get_kill_switch_status()
                or status[5].get() or not status[3].get()):
                    if  not status[5].get():
                        status[5].set(True)
                        stop_text[0].set("Reset E-Stop")
                    else:
                        # tell all motors to halt and hold position
                        controllers[0].halt_and_hold()
                        controllers[1].halt_and_hold()
                        controllers[2].halt_and_hold()
                        controllers[3].halt_and_hold()
                        controllers[4].halt_and_hold()
                        
                        # tell all motors to enter safe start so they dont heat up too much 
                        controllers[0].enter_safe_start()
                        controllers[1].enter_safe_start()
                        controllers[2].enter_safe_start()
                        controllers[3].enter_safe_start()
                        controllers[4].enter_safe_start()
                    messagebox.showinfo(
                        "Attention!",
                        "E-Stop pressed on GUI, All moition stopped. "
                        + "Please attempt to reset position of arm "
                        + "by manually moving axis slowly while powered down "
                        + "and resetting the pi and controllers. "
                        + "OR Another opition is to reset the e-stop to regain control "
                        + "and use a combination of moving the axis using by setting the "
                        + "position and pressing the move arm button. ",
                    )
                    return
            if not status[4].get():
                break
        # if an estop is pressed or the user unclicks the 
        if (
            controllers[axis_num - 1].get_kill_switch_status()
            or status[5].get()
            or not status[3].get()
        ):
            if  not status[5].get():
                status[5].set(True)
                stop_text[0].set("Reset E-Stop")
            else:
                # tell all motors to halt and hold position
                controllers[0].halt_and_hold()
                controllers[1].halt_and_hold()
                controllers[2].halt_and_hold()
                controllers[3].halt_and_hold()
                controllers[4].halt_and_hold()
                        
                # tell all motors to enter safe start so they dont heat up too much 
                controllers[0].enter_safe_start()
                controllers[1].enter_safe_start()
                controllers[2].enter_safe_start()
                controllers[3].enter_safe_start()
                controllers[4].enter_safe_start()
            messagebox.showinfo(
                "Attention!",
                "E-Stop pressed on GUI, All moition stopped. "
                + "Please attempt to reset position of arm "
                + "by manually moving axis slowly while powered down "
                + "and resetting the pi and controllers. "
                + "OR Another opition is to reset the e-stop to regain control "
                + "and use a combination of moving the axis using by setting the "
                + "position and pressing the move arm button. ",
            )
            return
        time.sleep(step_speed)


def findImportantControlPoints(commands: "list[dict]"):
    newCommmands = commands.copy
    temp_axis_num_list = list()
    temp_position_list = list()
    gripper_state_list = list()

    for i in range(0, len(commands)):
        temp_axis_num_list.append(commands[i]["AxisNum"])
        temp_position_list.append(commands[i]["Position"])
        gripper_state_list.append(commands[i]["Gripper State"])
    commands.clear()
    n = len(temp_position_list) - 1
    for i in range(0, n):
        if temp_axis_num_list[i] != temp_axis_num_list[i + 1] and i < n - 1:
            commands.append(
                {
                    "AxisNum": temp_axis_num_list[i],
                    "Position": temp_position_list[i],
                    "Gripper State": gripper_state_list[i],
                }
            )
            if temp_axis_num_list[i+1] == temp_axis_num_list[i + 2] and temp_axis_num_list[i + 2] != temp_axis_num_list[i + 3] and i < n - 3:
                commands.append(
                    {
                        "AxisNum": temp_axis_num_list[i+2],
                        "Position": temp_position_list[i+2],
                        "Gripper State": gripper_state_list[i+2],
                    }
                )
                i+=2
            ## INFO: Commenting this out improved play back function.     
            # commands.append(
            #     {
            #         "AxisNum": temp_axis_num_list[i + 1],
            #         "Position": temp_position_list[i + 1],
            #         "Gripper State": gripper_state_list[i + 1],
            #     }
            # )
            # i += 1
        elif gripper_state_list[i] != gripper_state_list[i + 1] and i < n:
            commands.append(
                {
                    "AxisNum": temp_axis_num_list[i],
                    "Position": temp_position_list[i],
                    "Gripper State": gripper_state_list[i],
                }
            )
        elif i == 0:
            if temp_position_list[0] != temp_position_list[1]:
                commands.append(
                    {
                        "AxisNum": temp_axis_num_list[i],
                        "Position": temp_position_list[i],
                        "Gripper State": gripper_state_list[i],
                    }
                )
        elif (
            0 < i
            and i < n - 1
            and temp_axis_num_list[i - 1]
            == temp_axis_num_list[i]
            == temp_axis_num_list[i + 1]
        ):
            if (
                temp_position_list[i - 1]
                > temp_position_list[i]
                < temp_position_list[i + 1]
            ):
                commands.append(
                    {
                        "AxisNum": temp_axis_num_list[i],
                        "Position": temp_position_list[i],
                        "Gripper State": gripper_state_list[i],
                    }
                )
            elif (
                temp_position_list[i - 1]
                < temp_position_list[i]
                > temp_position_list[i + 1]
            ):
                commands.append(
                    {
                        "AxisNum": temp_axis_num_list[i],
                        "Position": temp_position_list[i],
                        "Gripper State": gripper_state_list[i],
                    }
                )
        else:
            if temp_position_list[n - 1] != temp_position_list[n]:
                commands.append(
                    {
                        "AxisNum": temp_axis_num_list[i + 1],
                        "Position": temp_position_list[i + 1],
                        "Gripper State": gripper_state_list[i + 1],
                    }
                )
def keepActiveWhileMoving(axisNum):
    """Used to keep controllers awake while they are moving. 

    Args:
        axisNum (integer): used to select the desired axis
        newPosition (List[stringvars]): used to pass the new position text from the GUI to the controller
    """
    global controllers
    
    if axisNum == 1:
        try:
            controllers[axisNum - 1].reset_command_timeout()
            
        except:
            print("Error: axis", axisNum, " not responding, please check controller")
        
    elif axisNum == 2:
        try:
            controllers[axisNum].reset_command_timeout()
            controllers[axisNum - 1].reset_command_timeout()
        except:
            print("Error: axis", axisNum, " not responding, please check controller")
    else:
        try:
            controllers[axisNum].reset_command_timeout()
        except:
            print("Error: axis", axisNum, " not responding, please check controller")