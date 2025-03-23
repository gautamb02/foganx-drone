from djitellopy import Tello

class TelloControl:
    # Extracted constants for better readability and maintainability
    DEFAULT_DISTANCE = 30  # Default distance in cm
    DEFAULT_ANGLE = 30  # Default angle in degrees
    RESPONSE_TIMEOUT = Tello.RESPONSE_TIMEOUT  # Timeout for commands
    TAKEOFF_TIMEOUT = Tello.TAKEOFF_TIMEOUT  # Timeout for takeoff

    # Extracted direction constants
    DIRECTION_UP = "up"
    DIRECTION_DOWN = "down"
    DIRECTION_FORWARD = "forward"
    DIRECTION_BACKWARD = "back"
    DIRECTION_RIGHT = "right"
    DIRECTION_LEFT = "left"
    DIRECTION_ROTATE_LEFT = "ccw"  # Counter-clockwise
    DIRECTION_ROTATE_RIGHT = "cw"  # Clockwise

    TAKEOFF = "takeoff"
    LAND = "land"

    def __init__(self, tello: Tello):
        self.tello = tello
        self.isFlying = False  # camelCase for instance variable

    def connectDrone(self):
        """Connect to the Tello drone and print battery level."""
        print("Connecting to Tello...")
        self.tello.connect()
        print(f"Connected to Tello. Battery level: {self.tello.get_battery()}%")

    def takeOffDrone(self) -> bool:
        """Make the drone take off."""
        if self.tello.get_battery() <= 20:
            print("Drone can't take off. Low Battery.")
            return False
        if self.isFlying:
            print("Drone is already flying.")
            return False
        print("Taking off...")
        response = self.tello.send_control_command(self.TAKEOFF, self.TAKEOFF_TIMEOUT)
        if response:
            self.isFlying = True
            return True
        return False

    def landDrone(self) -> bool:
        """Land the drone."""
        if not self.isFlying:
            print("Drone is already on the ground.")
            return False
        print("Landing...")
        response = self.tello.send_control_command(self.LAND, self.RESPONSE_TIMEOUT)
        if response:
            self.isFlying = False
            return True
        return False

    def moveUp(self, distance: int = DEFAULT_DISTANCE) -> bool:
        """Move the drone up by a specified distance."""
        print(f"Moving up {distance} cm")
        return self._sendCommand(self.DIRECTION_UP, distance)

    def moveDown(self, distance: int = DEFAULT_DISTANCE) -> bool:
        """Move the drone down by a specified distance."""
        print(f"Moving down {distance} cm")
        return self._sendCommand(self.DIRECTION_DOWN, distance)

    def moveForward(self, distance: int = DEFAULT_DISTANCE) -> bool:
        """Move the drone forward by a specified distance."""
        print(f"Moving forward {distance} cm")
        return self._sendCommand(self.DIRECTION_FORWARD, distance)

    def moveBackward(self, distance: int = DEFAULT_DISTANCE) -> bool:
        """Move the drone backward by a specified distance."""
        print(f"Moving backward {distance} cm")
        return self._sendCommand(self.DIRECTION_BACKWARD, distance)

    def moveRight(self, distance: int = DEFAULT_DISTANCE) -> bool:
        """Move the drone right by a specified distance."""
        print(f"Moving right {distance} cm")
        return self._sendCommand(self.DIRECTION_RIGHT, distance)

    def moveLeft(self, distance: int = DEFAULT_DISTANCE) -> bool:
        """Move the drone left by a specified distance."""
        print(f"Moving left {distance} cm")
        return self._sendCommand(self.DIRECTION_LEFT, distance)

    def rotateLeft(self, angle: int = DEFAULT_ANGLE) -> bool:
        """Rotate the drone counter-clockwise by a specified angle."""
        print(f"Rotating left by {angle} degrees")
        return self._sendCommand(self.DIRECTION_ROTATE_LEFT, angle)
    
    def rotateRight(self, angle: int = DEFAULT_ANGLE) -> bool:
        """Rotate the drone counter-clockwise by a specified angle."""
        print(f"Rotating left by {angle} degrees")
        return self._sendCommand(self.DIRECTION_ROTATE_RIGHT, angle)

    def _sendCommand(self, command: str, value: int) -> bool:
        """Helper method to send a command to the drone."""
        try:
            response = self.tello.send_control_command(f"{command} {value}", self.RESPONSE_TIMEOUT)
            if not response:
                print(f"Failed to execute command: {command} {value}")
            return response
        except Exception as e:
            print(f"Error executing command: {command} {value}. Error: {e}")
            return False