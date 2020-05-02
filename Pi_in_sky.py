#Pi_in_sky.py
#flying project by Max Leblang and Elijah Tolton

from time import sleep
#controller library
from evdev import InputDevice, categorize, ecodes, KeyEvent
#motor library
import RPi.GPIO as GPIO
#data libraries
from datetime import datetime
import os
import csv
import threading
#sensor libraries
import Adafruit_LSM303
import Adafruit_BMP.BMP085 as BMP085

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup() #cleaning up GPIO output to get rid of errors
#Creating data file
now = datetime.now()
file_name = str(now.strftime("%Y-%m-%d_%H:%M:%S")) + ".csv"
os.mknod(file_name)

#dc motors
motors = {
    "20": False, #right
    "21": False, #Left
    "23": False, #Down
    "24": False  #Up
}
#variables for stick values
STICK_CENTER = 32768 #center is 32768
STICK_CUSHION = 15000 #creating 30000 dead-zone
#Variables to store accel data
sensor_data = []

#setup GPIO pins
GPIO.setup(24, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
#setup LSM303 instance
lsm303 = Adafruit_LSM303.LSM303()
bmp = BMP085.BMP085()
#setup read from controller in /dev/input
#Xbox controller is event2
dev = InputDevice('/dev/input/event2')
print(dev)

#function to collect accel data
def dataCollecter():
    while True:
        #Reading the X,Y,Z acceleration data
        accel, mag = lsm303.read()
        #Reading Altitude data
        temp = bmp.read_temperature()
        pressure = bmp.read_pressure()
        alt = bmp.read_altitude()
        #storing data
        sensorData_tuple = (accel[0],accel[1],accel[2],temp,pressure,alt)
        sensor_data.append(sensorData_tuple)
        #print("adding data")
        sleep(.1)
#threading dataCollecter so that we can control blimp and collect data at the same time        
dataThread = threading.Thread(target=dataCollecter)
dataThread.start()

#Reading contoller input
for event in dev.read_loop():
    #buttons
    if event.type == ecodes.EV_KEY:
        Button = categorize(event)
        #key is pressed to avoid registering key_up as well
        if Button.keystate == KeyEvent.key_down:
            #Y-button for saving data
            if Button.keycode[1] == "BTN_Y":
                #open flight data sheet
                print("Saving...")
                with open(file_name, mode='a+') as flight_data:
                    flight_writer = csv.writer(flight_data, delimiter=',')
                    #looping through tuples in list and storing into csv file
                    for (x,y,z,t,p,a) in sensor_data:
                        #data format is [accel_x,accel_y,accel_z,temp,pressure,altitude]
                        flight_writer.writerow([str(x), str(y), str(z), str(t), str(p), str(a)])
                flight_data.close()
                accel_data = []
                print("Complete!")
    
    #Joysticks
    elif event.type == ecodes.EV_ABS:
        #right joystick
        if event.code == ecodes.ABS_Z: #right stick X
            if event.value >= STICK_CENTER + STICK_CUSHION:#right
                #print("right")
                motors["20"] = True
            elif event.value <= STICK_CENTER - STICK_CUSHION:#left
                #print("left")
                motors["21"] = True
            else:
                #print("center")
                motors["20"] = False
                motors["21"] = False
        if event.code == ecodes.ABS_RZ: #right stick Y
            if event.value >= STICK_CENTER + STICK_CUSHION:#down
                #print("down")
                motors["24"] = False
                motors["23"] = True
            elif event.value <= STICK_CENTER - STICK_CUSHION:#up
                #print("up")
                motors["24"] = True
                motors["23"] = False
            else:
                #print("center")
                motors["24"] = False
                motors["23"] = False
        #left joystick        
        if event.code == ecodes.ABS_Y: #left stick Y
            if event.value <= STICK_CENTER - STICK_CUSHION:#forward
                #print("forward")
                motors["20"] = True
                motors["21"] = True
            else:
                #print("center")
                motors["20"] = False
                motors["21"] = False        
        #writing to motors
        for motor, state in motors.items():
            GPIO.output(int(motor), state)
            #print("Motor: {0} \t State: {1}".format(motor,state))

