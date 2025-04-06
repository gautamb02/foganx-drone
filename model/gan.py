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
from ultralytics import YOLO

FRAME_QUEUE = queue.Queue(maxsize=5)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
person_model_path = "./model/saved_models/person_model.pt"
person_model = YOLO(person_model_path).to(device)

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
        expected_frame = 0
        buffer = {}
        debug_frame_saved = False

        while not self.stop_event.is_set():
            try:
                priority, img = self.result_queue.get(timeout=1)

                if priority is None:
                    logger.debug("[Display] Sentinel received, stopping.")
                    break

                frame_number = priority
                self.result_queue.task_done()
                logger.debug(f"[Display] Received frame {frame_number}")

                # Resize the combined image for display
                img_resized = cv2.resize(img, (1600, 800))

                # # Save a debug frame just once
                # if not debug_frame_saved:
                #     cv2.imwrite("debug_frame.jpg", img_resized)
                #     debug_frame_saved = True
                #     logger.debug("[Display] Saved debug frame to disk")

                if frame_number != expected_frame:
                    buffer[frame_number] = img_resized
                    logger.debug(f"[Display] Buffered frame {frame_number}, waiting for {expected_frame}")
                    while expected_frame in buffer:
                        cv2.imshow("Processed Video", buffer.pop(expected_frame))
                        expected_frame += 1
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            logger.debug("[Display] 'q' pressed. Stopping display.")
                            self.stop_event.set()
                            break
                else:
                    logger.debug(f"[Display] Displaying expected frame {frame_number}")
                    cv2.imshow("Processed Video", img_resized)
                    expected_frame += 1
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.debug("[Display] 'q' pressed. Stopping display.")
                        self.stop_event.set()
                        break

                # Maintain consistent FPS
                current_time = time.time()
                time_since_last_frame = current_time - last_display_time
                if time_since_last_frame < FRAME_INTERVAL:
                    time.sleep(FRAME_INTERVAL - time_since_last_frame)
                last_display_time = time.time()

            except queue.Empty:
                logger.warning("[Display] Result queue is empty, waiting for frames.")
                continue

            except Exception as e:
                logger.error(f"[Display] Exception occurred: {e}")
                self.stop_event.set()
                break

        cv2.destroyAllWindows()
        logger.debug("[Display] Display worker stopped.")

    def preprocess_frame(self, frame):
        # Keep in RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (512, 512))
        logger.debug(f"resized image: {frame_resized.shape}")
        # Normalize to [-1, 1] range which is common for GANs
        img_tensor = torch.tensor(frame_resized / 127.5 - 1.0, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
        return img_tensor.cuda()

    def postprocess_frame(self, input_tensor, output_tensor, results):
        try:
            # Denormalize from [-1, 1] to [0, 255] and keep in RGB
            input_img = ((input_tensor[0].cpu().numpy().transpose(1, 2, 0) + 1.0) * 127.5).astype(np.uint8)
            output_img = ((output_tensor[0].cpu().numpy().transpose(1, 2, 0) + 1.0) * 127.5).astype(np.uint8)

            output_img = np.ascontiguousarray(output_img) 

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]
                    # Draw in RGB format
                    cv2.rectangle(output_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Match shapes
            if input_img.shape != output_img.shape:
                output_img = cv2.resize(output_img, (input_img.shape[1], input_img.shape[0]))

            # Return in RGB format
            return np.hstack((input_img, output_img))

        except Exception as e:
            logger.error(f"Error in postprocess_frame: {str(e)}")
            return input_tensor[0].cpu().numpy().transpose(1, 2, 0)  # Fallback image

    def infer_worker(self, worker_id):
        logger.debug(f"[FrameProcessor-{worker_id}] Worker started.")
        retry_count = 0
        max_retries = 3
        
        while not self.stop_event.is_set():
            try:
                frame_number, frame = FRAME_QUEUE.get(timeout=1)
                if frame_number is None:  # Check for sentinel value
                    logger.debug(f"[FrameProcessor-{worker_id}] Received sentinel, stopping.")
                    break

                if frame is None:
                    logger.warning(f"[FrameProcessor-{worker_id}] Received None frame, skipping")
                    FRAME_QUEUE.task_done()
                    continue

                try:
                    img_tensor = self.preprocess_frame(frame)
                    output_tensor = self.model_handler.infer(img_tensor)

                    results = person_model.predict(output_tensor, verbose=False)
                    logger.debug(f"[FrameProcessor-{worker_id}] Processing frame {frame_number}")
                    combined_frame = self.postprocess_frame(img_tensor, output_tensor, results)

                    self.result_queue.put((frame_number, combined_frame))
                    retry_count = 0  # Reset retry count on success

                except Exception as e:
                    logger.error(f"[FrameProcessor-{worker_id}] Error processing frame: {str(e)}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"[FrameProcessor-{worker_id}] Max retries reached, skipping frame")
                        retry_count = 0
                    else:
                        # Put the frame back in the queue for retry
                        FRAME_QUEUE.put((frame_number, frame))
                    continue

                FRAME_QUEUE.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[FrameProcessor-{worker_id}] Error in worker loop: {str(e)}")
                continue

        logger.debug(f"[FrameProcessor-{worker_id}] Worker stopped.")


class StreamProcessorApp:
    def __init__(self, camera_manager, model_path):
        self.camera_manager = camera_manager
        self.model_handler = ModelHandler(model_path)
        # self.frame_queue = 
        self.result_queue = queue.PriorityQueue(maxsize=5)
        self.stop_event = threading.Event()

    def start_processing(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            try:
                processor = FrameProcessor(self.model_handler, FRAME_QUEUE, self.result_queue, self.stop_event)

                # Start display thread
                executor.submit(processor.show_side_by_side)

                # Start worker threads
                # worker_futures = []
                for i in range(3):    
                    executor.submit(processor.infer_worker, i)

                frame_id = 0
                frame_counter = 0

                while not self.stop_event.is_set():
                    try:
                        if frame_counter % 3 == 0:
                            frame = self.camera_manager.get_frames()
                            if frame is not None:
                                FRAME_QUEUE.put((frame_id, frame))
                                frame_id += 1
                                logger.debug(f"[StreamProcessorApp] Added frame {frame_id} to queue")
                            else:
                                logger.warning("[StreamProcessorApp] Received None frame from camera")

                    except queue.Full:
                        logger.warning("[StreamProcessorApp] Frame queue is full, dropping frame")
                    except Exception as e:
                        logger.error(f"[StreamProcessorApp] Error getting frame: {str(e)}")
                    finally:
                        frame_counter += 1
                        time.sleep(0.01)  # Small delay to prevent CPU overuse

            except KeyboardInterrupt:
                logger.info("[StreamProcessorApp] Interrupted by user.")
                self.stop_event.set()

            except Exception as e:
                logger.error(f"[StreamProcessorApp] Error in start_processing: {str(e)}")
                raise e

            finally:
                self.stop_event.set()
                # Send sentinel values to stop workers
                for _ in range(3):
                    FRAME_QUEUE.put((None, None))
                
                cv2.destroyAllWindows()
