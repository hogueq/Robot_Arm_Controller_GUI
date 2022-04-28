#!/usr/bin/env bash
export DISPLAY=:0.0
sudo killall pigpiod
sudo systemctl start pigpiod
export PIGPIO_ADDR=192.168.1.10
export PIGPIO_PORT=8888
cd ~/Desktop/Robot_Arm_Controller_GUI