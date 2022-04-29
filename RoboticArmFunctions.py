#
# File: RoboticArmFunctions.py
# Date: 04/28/2022
# Author: Quinn Hogue
# Purpose: Functions and Control Logic For Robotic Arm
#

# imports
import json
import time
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
# Note: Could be done with a for loop
tic_axis1_1 = TicI2C(StepperControllerFunctions.bus, axis1_1_address)
tic_axis2_1 = TicI2C(StepperControllerFunctions.bus, axis2_1_address)
tic_axis2_2 = TicI2C(StepperControllerFunctions.bus, axis2_2_address)
tic_axis3_1 = TicI2C(StepperControllerFunctions.bus, axis3_1_address)
tic_axis4_1 = TicI2C(StepperControllerFunctions.bus, axis4_1_address)

# Set up the Servo Used for the Gripper
factory = PiGPIOFactory(host="localhost") 
''' Uses the pigpio_ library to interface to the Pi's GPIO pins. 
    This is done over a network socket which is why a host is required'''
gripper = Servo(
    12, # the pin number that the pwm signal will be output through
    pin_factory=factory, # sets the pin factory
    min_pulse_width=0.45 / 1000, # sets the open position for the gripper 
    max_pulse_width=1.1 / 1000, # sets the closed position for the gripper
    frame_width=20 / 1000, # the carrier frequency of the pwm signal 
)
"""min_pulse_width sets the close postion, max_pulse_width sets the open position - For Gripper Servo"""

controllers = [tic_axis1_1, tic_axis2_1, tic_axis2_2, tic_axis3_1, tic_axis4_1]
"""Axis1,Axis2_1,Axis2_2,Axis3,Axis4"""

# section not complete
# Will not be implemented by Team 7 Class of 2022, but may be used by futurestudents
# It will require feedback or limitswitches for this to be implimented
def homeArm():
    """Will be used for the section of code the preforms the homing of the robotic arm."""
    pass


staticmethod
def continuousCtrlLoop(
    current_positions: "list[DoubleVar]",
    new_positions: "list[DoubleVar]",
    status: "list[BooleanVar]",
    program_controls_text: "list[StringVar]",
    out_file=None,
):
    """Used for the continuous control of the axis.

    Args:
        current_positions (list[StringVars]): Contains the Current Positions In Mutable Form
        new_positions (list[StringVars]): Contains the Set Positions In Mutable Form
        status (list[BooleanVars]): Contains the Status In Mutable Form
    """
    global controllers
    kill_switch = False
    temp_position = [0.0, 0.0, 0.0, 0.0]
    temp_gripper_state = status[2].get()
    data = list() # will be used to append dictionary's containing values to create the final json file
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
                initialdir="./RecordedPaths",
                filetypes=[("Json file", "*.json")],
                initialfile="*.json",
            )
            # check to see if an outfile was given if not it means the user pressed cancel. Set the record check box back to zero. 
            if out_file == None: 
                messagebox.showwarning('Attention!',"Error: File did not open or not given. Not recording!")
                status[1].set(False) # reset check box for record back to false. 
        # loop for incrementing through the 4 different axis inputs. counts from 1 - 4
        for i in range(1, 5):
            # if run is not enabled break out of loop in order to get back to idle pause loop. 
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
                    # sets temp_position to the new position that was just sent to the controllers
                    temp_position[i - 1] = new_positions[i - 1].get()  
                    # sets temp grip to new state
                    temp_gripper_state = status[2].get()
            updateCurVal(current_positions) # call the function to update the current position of the arm
            
            # try get the status of the kill switch if it fails the a message 
            # will print out letting user know there is something wrong
            try:
                # if the controller kill switch is true or the e-stop status from the GUI is true
                if controllers[i].get_kill_switch_status() == True or status[5].get():
                    kill_switch = True # set killswitch variable to true
                    status[4].set(False) #set the run state to false 
                    program_controls_text[1].set("Run") # change the text back to run
                    if  not status[5].get(): # if the estop was not set on the screen 
                        status[5].set(True) # set the estop to true and change text to reset estop
                        program_controls_text[0].set("Reset E-Stop")
                        
                    else:
                        # command all controller to halt and hold
                        controllers[0].halt_and_hold()
                        controllers[1].halt_and_hold()
                        controllers[2].halt_and_hold()
                        controllers[3].halt_and_hold()
                        controllers[4].halt_and_hold()   
                        # command all controller to enter safe start
                        controllers[0].enter_safe_start()
                        controllers[1].enter_safe_start()
                        controllers[2].enter_safe_start()
                        controllers[3].enter_safe_start()
                        controllers[4].enter_safe_start()
                    break # break out of loop
            except: # the pi failed to communitcate to the the controller while in the control loop
                msg = str(
                    "Error: Not responding. Could not get_kill_switch_status(),"+
                    " please check controller.\nThen restart Live Axis Control"
                )
                messagebox.showwarning(title="Attention!!", message=msg) # error message popup on screen
                # if record is enabled and outfile is not none and not closed:
                # then write data to the json file and close. 
                if not status[1].get() and out_file != None and not out_file.closed:  
                    json.dump(data, out_file) 
                    out_file.close() # close the file to ensure the data gets written
                return
            
            # if record is enabled and outfile is not none and not closed:
            # then write data to the json file and close it used if the state switches while in the loop
            if not status[1].get() and out_file != None and not out_file.closed:
                json.dump(data, out_file)
                out_file.close()
        #breaks out of outter loop if killswitch is true
        if kill_switch:
            break
        
    #prompts user to continue the what they were doing. 
    if kill_switch:
        if messagebox.askretrycancel(
            title="Attention!!", message="Kill Switch Pressed, Motion Stopped"
        ):  
            program_controls_text[0].set("E-Stop") # resets the text for the estop
            status[5].set(False) #put the estop back to false
            # call itself to start the loop again
            continuousCtrlLoop(current_positions, new_positions, status, program_controls_text, out_file)
            if out_file != None and not out_file.closed:
                json.dump(data, out_file)
                out_file.close()
            return
        else:
            # pop up an info message about how to reset the position of the robotic arm. 
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
    # make sure if there is an out file it gets written out. 
    if out_file != None and not out_file.closed:
        json.dump(data, out_file)
        out_file.close()
    return



staticmethod
def ctrlLoop(
    current_positions: "list[DoubleVar]",
    new_positions: "list[DoubleVar]",
    status: "list[BooleanVar]",
    program_controls_text: "list[StringVar]"):
    """Used to send commands to each individual axis

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
                # try get the status of the kill switch if it fails the a message 
                # will print out letting user know there is something wrong
                try:
                    # if the controller kill switch is true or the e-stop status from the GUI is true
                    if controllers[i].get_kill_switch_status() == True or status[5].get():
                        kill_switch = True
                        if  not status[5].get(): # if the estop was not set on the screen 
                            status[5].set(True) # set the estop to true and change text to reset estop
                            program_controls_text[0].set("Reset E-Stop")
                        else:
                            # command all controller to halt and hold
                            controllers[0].halt_and_hold()
                            controllers[1].halt_and_hold()
                            controllers[2].halt_and_hold()
                            controllers[3].halt_and_hold()
                            controllers[4].halt_and_hold()   
                            # command all controller to enter safe start
                            controllers[0].enter_safe_start()
                            controllers[1].enter_safe_start()
                            controllers[2].enter_safe_start()
                            controllers[3].enter_safe_start()
                            controllers[4].enter_safe_start()
                        break
                except: # the pi failed to communitcate to the the controller while in the control loop
                    msg = str(
                        "Error: Controller responding. Could not get_kill_switch_status(), "+
                        "please check controller.\nThen attemp to press move arm again"
                    )
                    messagebox.showwarning(title="Attention!!", message=msg)# error message popup on screen
                    return
                # if the axis has reached the new position then exit loop
                if new_positions[i-1].get() == current_positions[i-1].get():
                    break
                # if the axis is not responding continue
                elif execution_time > 15.0:
                    break
            time.sleep(1) # wait 1 second
            #break out of outer loop if the killswitch is pressed
            if kill_switch:
                break

        # check to see if killswitch was pressed
        if kill_switch:
            if messagebox.askretrycancel(
                title="Attention", message="Kill Switch Pressed, Motion Stopped! GUI Reset must be pressed"
            ):
                program_controls_text[0].set("E-Stop") # resets the text for the estop
                status[5].set(False) #put the estop back to false
                ctrlLoop(current_positions, new_positions, status, program_controls_text)
                return
            else:
                # pop up an info message about how to reset the position of the robotic arm. 
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
                return

staticmethod
def updateCurVal(cur_val_vars: "list[DoubleVar]"):
    """Used to pull the current position values from the stepper controllers
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
        )  # 0.05625 degrees/step (4 axis controller is set set for 1/32step mode)
    except:
        print("Error: axis 4 not responding, check controller!")


# TODO: add in safer control code by adding limit check conditions
# should not be necessary, but I will include this recommendation anyway
staticmethod
def axisControl(axis_num: int, new_position: "list(DoubleVar)"):
    """Used to set new target positions for each axis
    
    Args:
        axis_num (int): used to select the desired axis
        new_position (list(DoubleVar)): used to pass the new position text from the GUI to the controller
    """
    global controllers
    target_1 = int(new_position[axis_num - 1].get() / 0.018) #set target value based off of the value of 
    if axis_num == 1:
        try:
            controllers[axis_num - 1].set_target_position(target_1) # sets the target position
            controllers[axis_num - 1].exit_safe_start() # tells the controller to exit safe start
        except:
            print("Error: axis", axis_num, " not responding, please check controller")
        # print("axis", axisNum, " target:", target_1)  #uncomment to have the targets print in the console when running from console
    elif axis_num == 2:
        target_2 = -target_1
        try:
            controllers[axis_num].set_target_position(target_2) # sets the target position
            controllers[axis_num - 1].set_target_position(target_1) # sets the target position it is the inverse of the other motor
            controllers[axis_num].exit_safe_start()# tells the controller to exit safe start
            controllers[axis_num - 1].exit_safe_start()# tells the controller to exit safe start
        except:
            print("Error: axis", axis_num, " not responding, please check controller")
        # print("axis", axisNum, " target:", target_1) #uncomment to have the targets print in the console when running from console
    else:
        if (
            axis_num == 4
        ):  # used to fixed the number before it is sent to the controller for the forth axis
            target_1 = int(target_1 / 3.125)
        # print("axis", axisNum, " target:", target_1) #uncomment to have the targets print in the console when running from console
        try:
            controllers[axis_num].set_target_position(target_1)# sets the target position
            controllers[axis_num].exit_safe_start()# tells the controller to exit safe start
        except:
            print("Error: axis", axis_num, " not responding, please check controller")


staticmethod
def gripActivate():
    """Function closes the gripper"""
    gripper.min() 
    time.sleep(1.0) # wait 1 second 


staticmethod
def gripDeactivate():
    """Function opens the grippers"""
    gripper.max()
    time.sleep(1.0) # wait 1 second


staticmethod
def set_current_position(axis_num, current_position, axis_setval_list, axis_curval_list):
    """Used to set new current position (Zero the position of the specified axis) 
        can be used to set other values for position values. Only used to zero axis in this code.
    Args:
        axisNum (interger): used to select the desired axis
        currentPosition (interger): used to pass the new current position from the GUI to the controller
    """
    global controllers # allows axis to the modules global var controllers
    target_1 = int(current_position / 0.018) # sets the target position that the controller will be set when it halts
    if axis_num == 1:
        try:
            controllers[axis_num - 1].set_current_position(target_1) # sets the target position zero
        except:
            print("Error: axis", axis_num, " not responding, please check controller") #print error message if controller is not responding
            return
        axis_setval_list[axis_num - 1].set("0.0") # sets the position zero
         # print("axis", axisNum, " target:", target_1) #uncomment to have the targets print in the console when running from console
    elif axis_num == 2:
        target_2 = -target_1
        try:
            controllers[axis_num].set_current_position(target_2) # sets the target position zero
            controllers[axis_num - 1].set_current_position(target_1) # sets the target position zero
        except:
            print("Error: axis", axis_num, " not responding, please check controller") #print error message if controller is not responding
            return
        axis_setval_list[axis_num - 1].set("0.0") # sets the position zero
        # print("axis", axisNum, " target:", target_1) #uncomment to have the targets print in the console when running from console
    else:
        try:
            if (
                axis_num == 4
            ):  # used to fixed the number before it is sent to the controller for the forth axis
                target_1 = int(target_1 / 3.125)
            controllers[axis_num].set_current_position(target_1)# sets the target position zero
        except:
            print("Error: axis", axis_num, " not responding, please check controller") #print error message if controller is not responding
            return
        axis_setval_list[axis_num - 1].set("0.0")# sets the position zero
        # print("axis", axisNum, " target:", target_1) #uncomment to have the targets print in the console when running from console
    updateCurVal(
        axis_curval_list
    )  # call the function to update the current values on the display


staticmethod
def playBackMotion(
    current_positions: "list[DoubleVar]",
    step_speed, 
    status: "list[BooleanVar]", 
    program_controls_text: "list[StringVar]"
):
    """_summary_

    Args:
        current_positions (list[DoubleVar]): _description_
        step_speed (_type_): _description_
        status (list[BooleanVar]): _description_
        stop_text (list[BooleanVar]): _description_
    """
    commands: "list[dict]" #declare the type hint for the commands variable 
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
        initialdir="./RecordedPaths",
        filetypes=[("Json file", "*.json")],
    )
    
    try:
        commands = json.load(in_file)
    except:
        # print error message to console if json can't be loaded
        print("Error: could not load json file")
        return
    in_file.close  # after file load it can be closed
    
    # used to find the local min and local max, when axis num changes, 
    # or when gripper state changes. 
    # Note: recording the gripper state may have some issues
    findImportantControlPoints(commands)  
    temp_gripper_state = status[2].get()
    for i in range(0, len(commands)):
        while not status[4].get(): # stays in loop while paused 
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
                    status[4].set(False) # Sets the run button state back to false 
                    program_controls_text[1].set("Run") # sets the text back to run
                    if  not status[5].get():
                        status[5].set(True)
                        program_controls_text[0].set("Reset E-Stop")
                    else:
                        # tell all motors to halt and hold position
                        controllers[0].halt_and_hold()
                        controllers[1].halt_and_hold()
                        controllers[2].halt_and_hold()
                        controllers[3].halt_and_hold()
                        controllers[4].halt_and_hold()
                        
                        # tell all motors to enter safe start so they don't heat up too much 
                        controllers[0].enter_safe_start()
                        controllers[1].enter_safe_start()
                        controllers[2].enter_safe_start()
                        controllers[3].enter_safe_start()
                        controllers[4].enter_safe_start()
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
                    return
            if not status[4].get():
                break
        # if an estop is pressed or the user uncheck the 
        if (
            controllers[axis_num - 1].get_kill_switch_status()
            or status[5].get()
            or not status[3].get()
        ):
            if  not status[5].get():
                status[5].set(True)
                program_controls_text[0].set("Reset E-Stop")
            else:
                # tell all motors to halt and hold position
                controllers[0].halt_and_hold()
                controllers[1].halt_and_hold()
                controllers[2].halt_and_hold()
                controllers[3].halt_and_hold()
                controllers[4].halt_and_hold()
                        
                # tell all motors to enter safe start so they don't heat up too much 
                controllers[0].enter_safe_start()
                controllers[1].enter_safe_start()
                controllers[2].enter_safe_start()
                controllers[3].enter_safe_start()
                controllers[4].enter_safe_start()
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
            return
        time.sleep(step_speed)

staticmethod
def findImportantControlPoints(commands: "list[dict]"):
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
        elif (0 < i and i < n - 1
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
                
staticmethod
def keepActiveWhileMoving(axisNum):
    """Used to keep controllers awake while they are moving. 

    Args:
        axisNum (integer): used to select the desired axis
        newPosition (List[stringvars]): used to pass the new position text from the GUI to the controller
    """
    global controllers
    
    if axisNum == 1:
        try:
            controllers[axisNum - 1].reset_command_timeout()# makes sure the controller does not time out while moving. 
            
        except:
            print("Error: axis", axisNum, " not responding, please check controller")
        
    elif axisNum == 2:
        try:
            controllers[axisNum].reset_command_timeout()# makes sure the controller does not time out while moving. 
            controllers[axisNum - 1].reset_command_timeout()# makes sure the controller does not time out while moving. 
        except:
            print("Error: axis", axisNum, " not responding, please check controller")
    else:
        try:
            controllers[axisNum].reset_command_timeout()# makes sure the controller does not time out while moving. 
        except:
            print("Error: axis", axisNum, " not responding, please check controller")