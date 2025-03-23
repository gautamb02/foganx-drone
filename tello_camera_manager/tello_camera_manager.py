import threading
import time
from logger.log import logger

class TelloCameraManager:
    def __init__(self, tello):
        self.tello = tello
        self.frame_read = None
        self.streaming = False
        self.latest_frame = None
        self.lock = threading.Lock()

    def start_stream(self):
        self.tello.streamon()
        self.frame_read = self.tello.get_frame_read()
        self.streaming = True
        self.thread = threading.Thread(target=self._update_frames, daemon=True)
        self.thread.start()
        logger.info("Tello camera stream started.")

    def _update_frames(self):
        while self.streaming:
            if self.frame_read and self.frame_read.frame is not None:
                with self.lock:
                    self.latest_frame = self.frame_read.frame.copy()
            time.sleep(0.01)  # reduce CPU usage

    def get_current_frame(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def stop_stream(self):
        self.streaming = False
        time.sleep(0.5)
        self.tello.streamoff()
        logger.info("Tello camera stream stopped.")
