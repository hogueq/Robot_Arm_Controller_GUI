#
# File: StepperControllerFunction.py
# Date: 04/19/2022
# Author: Quinn Hogue
# Contact Info: quinnhogue24@gmail.com
# Purpose: Contain the source code for the I2C communication used with the 
#   Polulo TIC 249's used to control the stepper motor. These are the basic functions 
#   That I used for the contorll more info can be found at https://www.pololu.com/docs/0J71/12.9 
#   is the link for the base code that I used to get started. The User guide is found at: 
#   https://www.pololu.com/docs/0J71. For future groups I recommend looking at a lib that another 
#   user created for the that has a more complete library. It is found at: https://github.com/jphalip/ticlib
#

# Uses the smbus2 library to send and receive data from a Tic.
# Works on Linux with either Python 2 or Python 3.
#
# NOTE: The Tic's control mode must be "Serial / I2C / USB".
# NOTE: For reliable operation on a Raspberry Pi, enable the i2c-gpio
#   overlay and use the I2C device it provides (usually /dev/i2c-3).
# NOTE: You might nee to change the 'SMBus(3)' line below to specify the
#   correct I2C device.
# NOTE: You might need to change the 'address = 11' line below to match
#   the device number of your Tic.

from smbus2 import SMBus, i2c_msg

class TicI2C(object):
    def __init__(self, bus, address):
        self.bus = bus
        self.address = address

    # Sends the "Exit safe start" command.
    def exit_safe_start(self):
        command = [0x83]
        write = i2c_msg.write(self.address, command)
        self.bus.i2c_rdwr(write)
        
    #sets current position used to set
    def set_current_position(self,value):
        command = [0xEC,
                   value >> 0 & 0xFF,
                   value >> 8 & 0xFF,
                   value >> 16 & 0xFF,
                   value >> 24 & 0xFF]
        write = i2c_msg.write(self.address, command)
        self.bus.i2c_rdwr(write)
        
    # Sets the target position.
    #
    # For more information about what this command does, see the
    # "Set target position" command in the "Command reference" section of the
    # Tic user's guide.
    def set_target_position(self, target):
        command = [0xE0,
                   target >> 0 & 0xFF,
                   target >> 8 & 0xFF,
                   target >> 16 & 0xFF,
                   target >> 24 & 0xFF]
        write = i2c_msg.write(self.address, command)
        self.bus.i2c_rdwr(write)

    # Gets one or more variables from the Tic.
    def get_variables(self, offset, length):
        write = i2c_msg.write(self.address, [0xA1, offset])
        read = i2c_msg.read(self.address, length)
        self.bus.i2c_rdwr(write, read)
        return list(read)
    
    # resets command timeout
    def reset_command_timeout(self):
        command = [0x8C]
        write = i2c_msg.write(self.address, command)
        self.bus.i2c_rdwr(write)
        
    # used to enter safe start
    def enter_safe_start(self):
        command = [0x8F]
        write = i2c_msg.write(self.address, command)
        self.bus.i2c_rdwr(write)
        
    def halt_and_hold(self):
        command = [0x89]
        write = i2c_msg.write(self.address, command)
        self.bus.i2c_rdwr(write)
        
    # Gets the "Current position" variable from the Tic.
    def get_current_position(self):
        b = self.get_variables(0x22, 4)
        position = b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24)
        if position >= (1 << 31):
            position -= (1 << 32)
        return position
    
    #checks to see if kill switch goes active and returns the 
    #boolean which is the state of the kill switch
    def get_kill_switch_status(self):
        b = self.get_variables(0x02,2)
        error_status = b[0] + (b[1] << 8)
        list = format(error_status,'016b')
        return bool(int(list[12]))
    

# Open a handle to "/dev/i2c-3", representing the I2C bus.
bus = SMBus(3)

# Set up the devices for motor controllers 
# position = tic.get_current_position()
# print("Current position is {}.".format(position))

# new_target = 0 if position > 0 else 41000 #2full rotations
# print("Setting target position to {}.".format(new_target))
# tic.exit_safe_start()
# tic.set_target_position(new_target)
