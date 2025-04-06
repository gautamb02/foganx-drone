import cv2
import threading
class Frame:
    """ A simple class to wrap the frame, mimicking the Tello frame structure. """
    def __init__(self, frame):
        self.frame = frame

class SystemCameraManager:
    def __init__(self, camera_index=0):
        """
        Initialize the SystemCameraManager with a system webcam instance.
        
        Args:
            camera_index: The index of the system camera (default is 0 for the default webcam).
        """
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open the camera with index {self.camera_index}.")
        print(f"System camera (index {self.camera_index}) initialized.")

    def streamon(self):
        """Start the video stream from the system camera."""
        if not self.cap.isOpened():
            raise ValueError("Camera stream not opened.")
        print("System camera stream turned ON.")

    def streamoff(self):
        """Stop the video stream from the system camera."""
        self.cap.release()
        print("System camera stream turned OFF.")

    def get_frames(self):
        """
        Capture and return a frame from the system camera as a Frame object.
        
        Returns:
            numpy.ndarray: The captured frame from the system camera.
        """
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame from system camera.")
            return None
        return frame  # Return the frame directly as a numpy array

# Placeholder for StreamProcessorApp
class StreamProcessorApp:
    def __init__(self, camera_manager, model_path):
        """
        Initialize the StreamProcessorApp with the camera manager and model path.
        
        Args:
            camera_manager: An instance of the camera manager to fetch frames.
            model_path: Path to the trained model (placeholder for actual model processing).
        """
        self.camera_manager = camera_manager
        self.model_path = model_path
        self.is_running = False

    def start_processing(self):
        """Start processing frames from the camera."""
        self.is_running = True
        while self.is_running:
            frame_obj = self.camera_manager.get_frames()
            if frame_obj is not None:
                frame = frame_obj #.frame
                # Placeholder for model inference (this would be where you process the frame)
                print("Processing frame...")
                # Assuming you would run inference here using the model
                # result = model_inference(frame)
                # You can process the result here, like display or save the output
                cv2.imshow("Processed Feed", frame)  # Display processed frame
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def stop_processing(self):
        """Stop the processing loop."""
        self.is_running = False
        print("Stopping stream processing.")

# Example usage:
if __name__ == "__main__":
    # Initialize system camera manager
    camera_manager = SystemCameraManager(camera_index=0)  # Default webcam (index 0)

    # Turn on the camera stream
    camera_manager.streamon()

    # Initialize the StreamProcessorApp
    app = StreamProcessorApp(camera_manager, "./model/saved_models/generator.pt")

    # Start processing frames in a separate thread
    process_thread = threading.Thread(target=app.start_processing, daemon=True)
    process_thread.start()

    try:
        # Main thread can be used for other operations or to monitor status
        while True:
            time.sleep(1)  # Main thread can sleep or handle other tasks
            # Stop processing after some time or some condition
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # Clean up resources before exit
        app.stop_processing()
        camera_manager.streamoff()
        cv2.destroyAllWindows()
