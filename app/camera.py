"""
AsBuilt Lens — Camera Module
Handles video capture from webcam/IP camera and motion stability detection.
"""

import cv2
import time
import logging
import numpy as np
from typing import Optional, Tuple

from config import (
    CAMERA_URL, CAMERA_SOURCE_LOCAL,
    STABILITY_THRESHOLD, STABILITY_FRAMES,
    CAPTURE_RESOLUTION
)

logger = logging.getLogger(__name__)


class CameraManager:
    """
    Manages video capture from local webcam or IP camera (DroidCam/IP Webcam).
    Provides motion stability detection for automatic capture.
    """

    def __init__(self, source: str = "local"):
        """
        Initialize camera manager.

        Args:
            source: "local" for laptop webcam, "ip" for IP camera URL
        """
        self.source = source
        self.cap: Optional[cv2.VideoCapture] = None
        self.prev_frame: Optional[np.ndarray] = None
        self.stable_count: int = 0
        self.is_connected: bool = False

    def connect(self) -> bool:
        """
        Open the camera connection.
        Returns True if successful, False otherwise.
        """
        try:
            if self.source == "local":
                self.cap = cv2.VideoCapture(CAMERA_SOURCE_LOCAL)
            else:
                self.cap = cv2.VideoCapture(CAMERA_URL)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera source: {self.source}")
                self.is_connected = False
                return False

            # Set resolution and minimize buffer latency
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_RESOLUTION[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_RESOLUTION[1])
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Minimizes lag

            self.is_connected = True
            self.prev_frame = None
            self.stable_count = 0
            logger.info(f"Camera connected: {self.source}")
            return True

        except Exception as e:
            logger.error(f"Camera connection error: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Release the camera connection."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_connected = False
        self.prev_frame = None
        self.stable_count = 0
        logger.info("Camera disconnected")

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from the camera.
        Returns the frame as numpy array (BGR), or None if failed.
        """
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            logger.warning("Failed to read frame from camera")
            return None

        return frame

    def check_stability(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Check if the current frame is stable (no significant motion).

        Uses frame differencing to detect motion. When consecutive frames
        show minimal difference for STABILITY_FRAMES count, the object
        is considered stable.

        Args:
            frame: Current frame (BGR numpy array)

        Returns:
            Tuple of (is_stable: bool, motion_score: float)
        """
        # Convert to grayscale for comparison
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            self.stable_count = 0
            return False, 1.0

        # Calculate absolute difference
        diff = cv2.absdiff(self.prev_frame, gray)
        motion_score = np.mean(diff) / 255.0  # Normalize to 0-1

        self.prev_frame = gray

        if motion_score < STABILITY_THRESHOLD:
            self.stable_count += 1
        else:
            self.stable_count = 0

        is_stable = self.stable_count >= STABILITY_FRAMES
        return is_stable, motion_score

    def capture_stable_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame and check stability.
        Returns the frame only when stability is confirmed, None otherwise.
        """
        frame = self.read_frame()
        if frame is None:
            return None

        is_stable, _ = self.check_stability(frame)
        if is_stable:
            self.reset_stability()
            return frame

        return None

    def reset_stability(self):
        """Reset stability counter to start fresh detection cycle."""
        self.stable_count = 0
        self.prev_frame = None

    def get_stability_progress(self) -> float:
        """
        Get current stability progress as percentage (0-100).
        Useful for UI progress indicator.
        """
        if STABILITY_FRAMES <= 0:
            return 100.0
        return min(100.0, (self.stable_count / STABILITY_FRAMES) * 100.0)

    @staticmethod
    def frame_to_rgb(frame: np.ndarray) -> np.ndarray:
        """Convert OpenCV BGR frame to RGB for display in Streamlit."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    @staticmethod
    def frame_to_pil(frame: np.ndarray):
        """Convert OpenCV BGR frame to PIL Image."""
        from PIL import Image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def test_camera_connection(source: str = "local") -> dict:
    """
    Quick test to verify camera connectivity.
    Returns dict with status, resolution, and sample frame.
    """
    cam = CameraManager(source=source)
    result = {
        "connected": False,
        "resolution": None,
        "frame": None,
        "error": None
    }

    try:
        if cam.connect():
            frame = cam.read_frame()
            if frame is not None:
                result["connected"] = True
                result["resolution"] = f"{frame.shape[1]}x{frame.shape[0]}"
                result["frame"] = frame
            else:
                result["error"] = "Connected but failed to read frame"
        else:
            result["error"] = "Failed to open camera"
    except Exception as e:
        result["error"] = str(e)
    finally:
        cam.disconnect()

    return result
