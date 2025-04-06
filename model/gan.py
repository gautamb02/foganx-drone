import threading
import queue
import time
import numpy
import cv2
import torch
import numpy as np
from model.generator import GeneratorResNet
from concurrent.futures import ThreadPoolExecutor
from logger.log import logger
from model.contants import FRAME_INTERVAL

class ModelHandler:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.load_model(model_path)

    def load_model(self, model_path):
        logger.debug("[ModelHandler] Loading model...")
        model = GeneratorResNet(input_nc=3, output_nc=3, ngf=64, n_blocks=4, img_size=512, light=True)
        model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        model.to(self.device).eval()
        logger.debug("[ModelHandler] Model loaded successfully!")
        return model

    def infer(self, tensor):
        with torch.no_grad():
            output = self.model(tensor.to(self.device))
            if isinstance(output, tuple):
                output = output[0]
            torch.cuda.synchronize()
            return output

class FrameProcessor:
    def __init__(self, model_handler, frame_queue, result_queue, stop_event):
        self.model_handler = model_handler
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.stop_event = stop_event

    def show_side_by_side(self):
        """ Displays processed frames side by side in order. """
        logger.debug("[Display] Display worker started.")
        last_display_time = time.time()
        expected_frame = 0  # The next frame number expected for display

        # Buffer for out-of-order frames
        buffer = {}

        while not self.stop_event.is_set():
            try:
                # Get the next available processed frame (ordered by frame number)
                frame_number, img = self.result_queue.get()
                logger.debug(f"[Display] Received frame {frame_number} from result queue.")
                self.result_queue.task_done()

                if frame_number is None:
                    logger.debug("[Display] Sentinel received, stopping.")
                    break

                # Resize the combined image so that each half is 800x800
                # (Assuming the combined image is a horizontal concatenation of two images)
                img_resized = cv2.resize(img, (1600, 800))

                # If the frame is not the expected one, store it in the buffer.
                if frame_number != expected_frame:
                    buffer[frame_number] = img_resized
                    # Try to output any buffered frames that are now in order.
                    while expected_frame in buffer:
                        cv2.imshow("Processed Video", buffer.pop(expected_frame))
                        expected_frame += 1
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            logger.debug("[Display] 'q' pressed. Stopping display.")
                            self.stop_event.set()
                            break
                else:
                    # If the frame is the expected one, display it
                    logger.debug("Show Processed video frame")
                    cv2.imshow("Processed Video", img_resized)
                    expected_frame += 1

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.debug("[Display] 'q' pressed. Stopping display.")
                        self.stop_event.set()
                        break

                # Maintain target FPS if needed
                current_time = time.time()
                time_since_last_frame = current_time - last_display_time
                if time_since_last_frame < FRAME_INTERVAL:
                    time.sleep(FRAME_INTERVAL - time_since_last_frame)
                last_display_time = time.time()

            except queue.Empty:
                logger.error("[Display] Result Queue is empty")

            except Exception as e:
                logger.error("[Display] Exception in show_side_by_side")
                raise e

        cv2.destroyAllWindows()
        print("DEBUG: [Display] Display worker stopped.")

    def preprocess_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (512, 512))
        logger.debug(f"resized image: {frame_resized.shape}")
        img_tensor = torch.tensor(frame_resized / 255.0, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
        return img_tensor.cuda()

    def postprocess_frame(self, input_tensor, output_tensor):
        try:
            # Ensure tensors are on CPU and convert to numpy
            input_img = input_tensor[0].cpu().numpy().transpose(1, 2, 0)
            output_img = output_tensor[0].cpu().numpy().transpose(1, 2, 0)
            
            # Ensure both images have the same shape
            if input_img.shape != output_img.shape:
                output_img = cv2.resize(output_img, (input_img.shape[1], input_img.shape[0]))
            
            # Combine images horizontally
            return np.hstack((input_img, output_img))
        except Exception as e:
            logger.error(f"Error in postprocess_frame: {str(e)}")
            # Return original input if processing fails
            return input_img

    def infer_worker(self, worker_id):
        print(f"[FrameProcessor-{worker_id}] Worker started.")
        
        while not self.stop_event.is_set():
            try:
                frame_number, frame = self.frame_queue.get(timeout=1)
            except queue.Empty:
                logger.debug("Queue Empty")
                continue

            img_tensor = self.preprocess_frame(frame)
            output_tensor = self.model_handler.infer(img_tensor)

            logger.debug(f"Output frame shape {output_tensor.shape}")
            combined_frame = self.postprocess_frame(img_tensor, output_tensor)

            self.result_queue.put((frame_number, combined_frame))
            self.frame_queue.task_done()
        print(f"[FrameProcessor-{worker_id}] Worker stopped.")


class StreamProcessorApp:
    def __init__(self, camera_manager, model_path):
        self.camera_manager = camera_manager
        self.model_handler = ModelHandler(model_path)
        self.frame_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.PriorityQueue(maxsize=5)
        self.stop_event = threading.Event()

    def start_processing(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            try:
                processor = FrameProcessor(self.model_handler, self.frame_queue, self.result_queue, self.stop_event)

                # worker threads
                for i in range(1, 3):    
                    executor.submit(processor.infer_worker, i)

                # display thread
                executor.submit( processor.show_side_by_side )
                frame_id = 0
                frame_counter = 0

                while not self.stop_event.is_set():
                    try:
                        if( frame_counter%3==0 ):
                            frame: numpy.ndarray = self.camera_manager.get_frames().frame 
                            self.frame_queue.put((frame_id, frame))                        
                            frame_id += 1

                    except queue.Full: 
                        logger.debug("Frame Queue is full")
                    finally:
                        frame_counter+=1

            except KeyboardInterrupt:
                print("[StreamProcessorApp] Interrupted by user.")
                self.stop_event.set()

            except Exception as e: 
                print("Error in start_processing")
                raise e

            finally:
                self.stop_event.set()
                for _ in range(3):
                    self.frame_queue.put((None, None))
                cv2.destroyAllWindows()
