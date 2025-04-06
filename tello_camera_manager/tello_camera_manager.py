import cv2
import time
from djitellopy import Tello

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
        

# if __name__ == "__main__":
#     tello = Tello()
#     tello.connect()
    
#     camera_manager = TelloCameraManager(tello=tello)
#     camera_manager.streamon()

#     try:
#         while True:
#             frame = camera_manager.get_frames().frame
#             if frame is not None:
#                 cv2.imshow("Tello Video Feed", frame)

#             # Exit on 'q' key press
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#     finally:
#         camera_manager.streamoff()
#         cv2.destroyAllWindows()
