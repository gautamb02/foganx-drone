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
import pygame 

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
    
    # Initialize PyGame
    pygame.init()
    screen = pygame.display.set_mode((300, 300))
    pygame.display.set_caption("Drone Control")
    clock = pygame.time.Clock()

    # Control mapping with original keys
    control_map = {
        pygame.K_w: lambda: controller.moveUp(30),
        pygame.K_s: lambda: controller.moveDown(30),
        pygame.K_a: lambda: controller.rotateLeft(30),
        pygame.K_d: lambda: controller.rotateRight(30),
        pygame.K_i: lambda: controller.moveForward(30),
        pygame.K_k: lambda: controller.moveBackward(30),
        pygame.K_j: lambda: controller.moveLeft(30),
        pygame.K_l: lambda: controller.moveRight(30),
        pygame.K_z: lambda: controller.takeOffDrone(),
        pygame.K_SLASH: lambda: controller.landDrone()
    }

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.K_q:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key in control_map:
                        print("Event CLick: ",event.key)
                        control_map[event.key]()

            # # Get all currently pressed keys
            # keys = pygame.key.get_pressed()
            # for key, action in control_map.items():
            #     if keys[key]:
            #         print(keys[key])
            #         action()

            # Limit the frame rate to reduce CPU usage
            clock.tick(30)

    except Exception as e:
        print(f"Error in drone control: {e}")
    finally:
        pygame.quit()
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
        logger.info(f"Drone connected. {tello.get_battery()}% battery.")
        thread = []

        controller = TelloControl(tello)
        camera_manager = TelloCameraManager(tello)
        camera_manager.streamon() # adding the image frames on a seperate thread
    
        # Start drone control in a separate thread
        controlThread = threading.Thread(target=droneControlFunc, args=(controller,), daemon=True)
        thread.append(controlThread)
        controlThread.start()        

        time.sleep(1)

        app = StreamProcessorApp(camera_manager, "./model/saved_models/generator.pt")
        # processThread = threading.Thread(target=app.start_processing, daemon=True)
        # thread.append(processThread)
        # processThread.start()
        app.start_processing()

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
