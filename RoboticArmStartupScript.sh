export DISPLAY=:0.0
sudo killall pigpiod
sudo systemctl start pigpiod
export PIGPIO_ADDR=localhost
export PIGPIO_PORT=8888
cd ~/Desktop/Robot_Arm_Controller_GUI
python3 main.py
