import threading
import time
import cv2
from djitellopy import Tello

class TelloControl:
    def __init__(self, tello : Tello):
        self.tello = tello

    def connectDrone(self):
        """Connect to Tello drone."""
        print("Connecting to Tello...")
        self.tello.connect()
        print(f"Connected to Tello, battery level: {self.tello.get_battery()}%")

    def takeOffDrone(self):
        """Make the drone take off."""
        print("Taking off...")
        self.tello.takeoff()

    def landDrone(self):
        """Land the drone."""
        print("Landing...")
        self.tello.land()

    def moveUpDrone(self, distance=30):
        """Move the drone up."""
        print(f"Moving up {distance} cm")
        self.tello.move_up(distance)

    def moveDownDrone(self, distance=30):
        """Move the drone down."""
        print(f"Moving down {distance} cm")
        self.tello.move_down(distance)

    def moveForwardDrone(self, distance=30):
        """Move the drone forward."""
        print(f"Moving forward {distance} cm")
        self.tello.move_forward(distance)

    def moveBackwardDrone(self, distance=30):
        """Move the drone back."""
        print(f"Moving back {distance} cm")
        self.tello.move_back(distance)

    def moveRightDrone(self, distance=30):
        """Move the drone right."""
        print(f"Moving right {distance} cm")
        self.tello.move_right(distance)

    def moveLeftDrone(self, distance=30):
        """Move the drone left."""
        print(f"Moving left {distance} cm")
        self.tello.move_left(distance)

    def rotateLeftDrone(self, angle=30):
        """Rotate the drone left (counter-clockwise)."""
        print(f"Rotating left by {angle} degrees")
        self.tello.rotate_counter_clockwise(angle)

    def rotateRightDrone(self, angle=30):
        """Rotate the drone right (clockwise)."""
        print(f"Rotating right by {angle} degrees")
        self.tello.rotate_clockwise(angle)

    def stream_video(self):
        """Start video streaming."""
        self.tello.streamon()
        while True:
            frame = self.tello.get_frame_read().frame
            cv2.imshow("Tello Camera Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    def stop_streaming(self):
        """Stop video streaming."""
        self.tello.streamoff()