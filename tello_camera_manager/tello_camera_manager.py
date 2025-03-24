import cv2
import time

class TelloCameraManager:
    def __init__(self, tello):
        """Initialize the TelloCameraManager with a Tello drone instance.
        
        Args:
            tello: The Tello drone instance

        """
        self.tello = tello
        self.frame_read = None

    def streamon(self):
        """Turn on the video stream from the Tello drone."""
        try:
            self.tello.streamon()
            # Use queue-based frame reading for better real-time performance
            self.frame_read = self.tello.get_frame_read()
            print("Tello camera stream turned ON.")
        except Exception as e:
            print(f"Failed to turn on stream: {e}")

    def streamoff(self):
        """Turn off the video stream from the Tello drone."""
        try:
            self.tello.streamoff()
            print("Tello camera stream turned OFF.")
        except Exception as e:
            print(f"Failed to turn off stream: {e}")

    def get_frames(self):
        """
        Return the frames
        """
        return self.frame_read
        
