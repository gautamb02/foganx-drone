import argparse
from configreader import config
from logger.log import logger
from network_manager.manager import TelloNetworkManager
from tello_mananger.tello_manager import TelloControl
from djitellopy import Tello
import time
import msvcrt
import threading

logger.info("Starting application")

global config_data 

def setUpConfig():
    global config_data
    parser = argparse.ArgumentParser(description="Read configuration file")
    parser.add_argument("--config", type=str, default="config.yml", help="Path to the config file")
    args = parser.parse_args()

    config_data = config.read_config(args.config)
    if config_data:
        logger.info("Config Loaded Successfully.")
        return True
    else:
        logger.fatal("Error reading in config.")
        return False
    
def setUpConnection(ssid, password):
    network_manager = TelloNetworkManager(ssid, password)
    ok = network_manager.connect_to_network()
    return ok



def droneControlFunc(controller: TelloControl):
    print("Drone control started. Use keys: w s a d i k j l z / (press q to exit)")

    def exit_control():
        print("Exiting control loop.")
        raise StopIteration  # Custom stop signal

    control_map = {
        'w': lambda: controller.moveUp(30),
        's': lambda: controller.moveDown(30),
        'a': lambda: controller.rotateLeft(30),
        'd': lambda: controller.rotateRight(30),
        'i': lambda: controller.moveForward(30),
        'k': lambda: controller.moveBackward(30),
        'j': lambda: controller.moveLeft(30),
        'l': lambda: controller.moveRight(30),
        'z': lambda: controller.takeOffDrone(),
        '/': lambda: controller.landDrone(),
        'q': exit_control  # This will trigger a graceful exit
    }

    try:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getwch().lower()
                action = control_map.get(key)
                if action:
                    # print(f"Executing command: {key}")
                    success = action()  # Execute the command and get the result
                    if not success:
                        print(f"Command failed: {key}")
                    # Block further input until the current command is complete
                    while msvcrt.kbhit():  # Clear any buffered key presses
                        msvcrt.getwch()
                else:
                    print(f"Invalid key: {key}. Try again.")
    except StopIteration:
        print("Drone control ended.")
    finally:
        if controller.isFlying:
            ok = controller.landDrone()

def main():

    ok = setUpConfig()
    if not ok:
        return
    
    # print(config_data.network.wifi)
    ok = setUpConnection(config_data.network.wifi.SSID, config_data.network.wifi.Password)

    if not ok:
        return
    tello = Tello()
    threads = []

    controller = TelloControl(tello) 
    controller.connectDrone()

    controllerThread = threading.Thread(target=droneControlFunc, args=(controller,), daemon=True)
    threads.append(controllerThread)
    controllerThread.start()

    for thread in threads:
        thread.join()

    logger.info("App Started.")
main()  