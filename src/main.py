import argparse
import sys
from configreader import config
from logger.log import logger
from network_manager.manager import TelloNetworkManager
from tello_mananger.tello_manager import TelloControl
from tello_camera_manager.tello_camera_manager import TelloCameraManager
from model.gan import StreamProcessorApp
from djitellopy import Tello
import time
import asyncio
import msvcrt
import threading
import cv2

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

def displayStream(camera_manager: TelloCameraManager):
    try:
        while True:
                frame = camera_manager.get_frames().frame

                if frame is not None:
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    cv2.imshow("Tello Video Stream - Original | Dehazed", rgb_image)

                # Keep-alive
                # self.tello.send_rc_control(0, 0, 0, 0)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
            logger.warning("Emergency landing due to keyboard interrupt.")

    finally:
        cv2.destroyAllWindows()
        logger.info("Camera stream stopped.")

def droneControlFunc(controller: TelloControl):
    print("Drone control started. Use keys: w s a d i k j l z / (press q to exit)")

    def exit_control():
        print("Exiting control loop.")
        raise StopIteration

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
        'q': exit_control
    }

    try:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getwch().lower()
                logger.error( key )
                # action = control_map.get(key)
                # if action:
                #     success = action()
                #     if not success:
                #         print(f"Command failed: {key}")
                #     while msvcrt.kbhit():
                #         msvcrt.getwch()  # Clear input buffer
                # else:
                #     print(f"Invalid key: {key}. Try again.")

            # time.sleep(0.000001)  # Give CPU some breathing room

    except StopIteration:
        print("Drone control ended.")
    finally:
        if controller.isFlying:
            controller.landDrone()

def main():
    tello = None
    try:
        if not setUpConfig():
            return

        if not setUpConnection(config_data.network.wifi.SSID, config_data.network.wifi.Password):
            return

        tello = Tello()
        tello.connect()
        logger.info("Drone connected.")
        thread = []

        controller = TelloControl(tello)
        camera_manager = TelloCameraManager(tello)
        camera_manager.streamon() # adding the image frames on a seperate thread

        # Start drone control in a separate thread
        # controlThread = threading.Thread(target=droneControlFunc, args=(controller,), daemon=True)
        # thread.append(controlThread)
        # controlThread.start()        

        app = StreamProcessorApp(camera_manager, "./model/saved_models/generator.pt")
        processThread = threading.Thread(target=app.start_processing, daemon=True)
        thread.append(processThread)
        processThread.start()

        # Wait for control thread to end (user presses q)
        for t in thread:
            t.join()

        # Stop camera after control ends
        camera_manager.streamoff()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise e
    finally:
        if tello:
            tello.end()
        cv2.destroyAllWindows()
        logger.info("Application closed gracefully.")

if __name__ == "__main__":
    main()
