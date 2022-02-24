import time
import evdev
import asyncio
import requests
import RPi.GPIO as GPIO


URL = ""
ENTRANCEPIN = 8
EXITPIN     = 10


def GPIO_setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD) # Pin number
    
    GPIO.setup(ENTRANCEPIN, GPIO.OUT)
    GPIO.output(ENTRANCEPIN, 0)
    GPIO.setup(EXITPIN, GPIO.OUT)
    GPIO.output(EXITPIN, 0)

def door_control(pin):
    GPIO.output(pin, 1)
    time.sleep(0.1)
    GPIO.output(pin, 0)        

def device_search():
    entranceHID = None
    exitHID = None
    
    for device in evdev.util.list_devices():
        dev = evdev.InputDevice(device)
        
        if dev.phys.split('/')[0][-1] == '3':
            entranceHID = dev
        elif dev.phys.split('/')[0][-1] == '4':
            exitHID = dev
            
    if not (entranceHID and exitHID): raise AssertionError("HID not detected")
    
    return entranceHID, exitHID

def send_hid_code(direction, keys):
    if direction == "out": door_control(EXITPIN)
    
    userHid = "".join(key[-1] for key in keys)
    parameter = {'user_hid': userHid, 'work_status': direction}
    res = requests.get(URL, params=parameter)
    if (res.status_code == 200) and direction == "in": door_control(ENTRANCEPIN)

    
async def monitor(device, direction):
    cnt = 0
    keys = []
    
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            cnt+=1
            key = evdev.categorize(event).keycode
            
            if cnt%2 == 0:
                if key == 'KEY_KPENTER':
                    send_hid_code(direction, keys)
                    keys = []
                    cnt = 0
                else:
                    keys.append(key)


if __name__ == "__main__":
    print("Start")
    
    GPIO_setup()
    entranceHID, exitHID = device_search()
    
    asyncio.ensure_future(monitor(entranceHID, "in"))
    asyncio.ensure_future(monitor(exitHID, "out"))
    
    loop = asyncio.get_event_loop()
    loop.run_forever()